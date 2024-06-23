import requests, os, zipfile, logging, hashlib, glob, shutil, yaml, datetime
from pprint import pprint
from flask import Flask, request

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('updater-config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Access values from the config file
cf_api_url = config['cf_api_url']
cf_api_key = config['cf_api_key']
modrinth_api_url = config['modrinth_api_url']
modrinth_api_key = config['modrinth_api_key']
my_api_key = config['app_api_key']
ntfy_url = config['ntfy_url']


# Functions
def fetchServerPack(project_id):
    headers = {'x-api-key': cf_api_key}
    response = requests.get(f'{cf_api_url}/mods/{project_id}', headers=headers)
    response.raise_for_status()  # Ensure we got a successful response
    data = response.json()
    logging.debug(pprint(data))
    latest_files = data['data']['latestFiles']
    latest_files.sort(key=lambda x: x['fileDate'], reverse=True)
    latest_file = latest_files[0]
    file_id = latest_file['serverPackFileId']
    return file_id

def fetchDownload(project_id,file_id):
    headers = {'x-api-key': cf_api_key}
    response = requests.get(f'{cf_api_url}/mods/{project_id}/files/{file_id}', headers=headers)
    response.raise_for_status()  # Ensure we got a successful response
    data = response.json()
    data = data['data']
    logging.debug(pprint(data))

    # Set variables from the API response
    download_url = data['downloadUrl']
    file_name = data['fileName']
    logging.info(f'Downloading file: {file_name} - {file_id}')
    response = requests.get(download_url)
    response.raise_for_status()

    # Save the file as file_id.zip
    file_path = f'../downloads/{file_id}.zip'
    with open(file_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Downloaded {file_name} from {download_url}')

    # Test the file hash with sha1
    file_hash = data['hashes'][0]['value']
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as file:
            # Read the file in chunks to avoid memory issues with large files
            while chunk := file.read(8192):
                sha1.update(chunk)
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"
    file_hash_sha1 = sha1.hexdigest()
    logging.info(f'Server hash: {file_hash}')
    logging.info(f'File hash (sha1): {file_hash_sha1}')
    if file_hash == file_hash_sha1:
        logging.info('File hash matches')
    else:
        logging.error('File hash does not match')
        if os.path.exists(file_path):
            os.remove(file_path)
        exit()
    return file_path

def fetchPlugin(id):
    headers = {'Authorization': modrinth_api_key}
    response = requests.get(f'{modrinth_api_url}/project/{id}/version', headers=headers)
    response.raise_for_status()  # Ensure we got a successful response
    data = response.json()
    logging.debug(pprint(data))
    sorted_data = sorted(data, key=lambda x: datetime.fromisoformat(x['date_published']), reverse=True)
    latest_version = sorted_data[0]
    latest_file_url = latest_version['files'][0]['url']
    file_name = latest_version['files'][0]['filename']
    file_hash = latest_version['files'][0]['sha1']
    logging.info(f'Founded latest file url: {file_name}')
    download = requests.get(latest_file_url)
    download.raise_for_status()
    with open(f'../downloads/{file_name}', 'wb') as file:
        file.write(download.content)
    logging.debug(f'Downloaded {file_name} from {latest_file_url}')
    sha1 = hashlib.sha1()
    try:
        with open(f'../downloads/{file_name}', 'rb') as file:
            # Read the file in chunks to avoid memory issues with large files
            while chunk := file.read(8192):
                sha1.update(chunk)
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"
    file_hash_sha1 = sha1.hexdigest()
    logging.debug(f'Server hash: {file_hash}')
    logging.debug(f'File hash (sha1): {file_hash_sha1}')
    if file_hash == file_hash_sha1:
        logging.info(f'{file_name} downloaded and hash matches')
    else:
        logging.error('File hash does not match')
        if os.path.exists(f'../downloads/{file_name}'):
            os.remove(f'../downloads/{file_name}')
        return
    logging.debug('Installing plugin')
    if not os.path.exists(f'../plugins/{file_name}'):
        os.makedirs('../plugins', exist_ok=True)
        shutil.copy(f'../downloads/{file_name}', f'../plugins/{file_name}')
        logging.debug(f'Installed {file_name}')
        os.remove(f'../downloads/{file_name}')
    else:
        logging.debug(f'{file_name} already installed')
        os.remove(f'../downloads/{file_name}')

def installFiles(file_path):
    # Move files matching the regex to a temp folder
    logging.info('Moving files to temp folder')
    os.makedirs('../temp/mods', exist_ok=True)
    os.makedirs('../temp/config', exist_ok=True)
    mods_patterns = ["BlueMap*", "bmm*", "Chunky*", "dcintergration*", "HuskHomes*", "InvView*", "ledger*", "LuckPerms*", "minimotd*", "tabtps*", "worldedit*"]
    config_patterns = ["BlueMap*", "Chunky*", "dcintergration*", "HuskHomes*", "Discord*", "ledger*", "LuckPerms*", "minimotd*", "tabtps*", "worldedit*", "do_a_barrel_roll-server*"]

    for pattern in mods_patterns:
        for file in glob.glob(f'../mods/{pattern}'):
            destination = os.path.join('mods', os.path.basename(file))
            shutil.move(file, destination)

    for pattern in config_patterns:
        for file in glob.glob(f'../config/{pattern}'):
            destination = os.path.join('config', os.path.basename(file))
            shutil.move(file, destination)

    # Delete the old mods folder and the config folder:
    logging.info('Deleting old mods and config folders')
    if os.path.exists('../mods'):
        os.system('rm -rf ../mods')
    if os.path.exists('../config'):
        os.system('rm -rf ../config')

    # Unzip the file if it's a zip file
    logging.info('Unzipping file')
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall('../')

    # Move the contents of temp/mods and temp/config into the /server/Minecraft/mods and /server/Minecraft/config folders
    logging.info('Moving temp/mods and temp/config into Minecraft folder')
    for file in glob.glob('../temp/mods/*'):
        shutil.move(file, '../mods')
    for file in glob.glob('../temp/config/*'):
        shutil.move(file, '../config')

    # Remove the zip file and the temp folder
    logging.info('Removing zip file and temp folder')
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists('../temp'):
        os.system('rm -rf ../temp')

# Main
app = Flask(__name__)

@app.route('/update', methods=['GET'])
def update():
    # Check if the correct API key was provided
    if request.headers.get('api_key') == my_api_key:
        project_id = request.args.get('project_id')
        logging.info(f'API hit from ip: {request.remote_addr}')
        logging.info('Fetching latest server pack file ID')
        server_file_id = fetchServerPack(project_id)
        logging.info(f'Latest file ID: {server_file_id}')
        # Download the file if it doesn't exist
        if not os.path.exists(f'../downloads/{server_file_id}.zip'):
            logging.info('Downloading...')
            file_path = fetchDownload(project_id,server_file_id)
        else:
            logging.info('File already exists')
            file_path = f'../downloads/{server_file_id}.zip'
        logging.info('Installing files')
        installFiles(file_path)
        logging.info('Sending ntfy message')
        message = f'Server update complete {server_file_id}'
        requests.post(ntfy_url,
            data=message,
            headers={
                "Title": "MC Server Update",
                "Tags": "white_check_box"
            })
        logging.info('Update complete')
        return 'Update complete', 200
    else:
        message=f"Invalid API key from ip: {request.remote_addr}"
        logging.error(message)
        requests.post(ntfy_url,
            data=message,
            headers={
                "Title": "MC Server Update",
                "Tags": "no_entry",
                "Priority": "5"
            })
        return 'Invalid API key', 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)