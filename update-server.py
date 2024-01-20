import requests, os, zipfile, logging, yaml, hashlib, glob, shutil
from pprint import pprint
from flask import Flask, request
from discord_webhook import DiscordWebhook

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set the base URL and your API key
base_url = os.environ['BASE_API_URL']
api_key = os.environ['CURSEFORGE_API_KEY']
project_id = os.environ['PROJECT_ID']
discord_webhook = os.environ['DISCORD_WEBHOOK_URL']


# Functions
def fetchServerPack():
    headers = {'x-api-key': api_key}
    response = requests.get(f'{base_url}/mods/{project_id}', headers=headers)
    response.raise_for_status()  # Ensure we got a successful response
    data = response.json()
    logging.debug(pprint(data))
    latest_files = data['data']['latestFiles']
    latest_files.sort(key=lambda x: x['fileDate'], reverse=True)
    latest_file = latest_files[0]
    file_id = latest_file['serverPackFileId']
    return file_id

def fetchDownload(file_id):
    headers = {'x-api-key': api_key}
    response = requests.get(f'{base_url}/mods/{project_id}/files/{file_id}', headers=headers)
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
    file_path = f'./{file_id}.zip'
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

def installFiles(file_path):
    # Move files matching the regex to a temp folder
    logging.info('Moving files to temp folder')
    os.makedirs('./temp/mods', exist_ok=True)
    os.makedirs('./temp/config', exist_ok=True)
    mods_patterns = ["BlueMap*", "bmm*", "Chunky*", "dcintergration*", "HuskHomes*", "InvView*", "ledger*", "LuckPerms*", "minimotd*", "tabtps*", "worldedit*"]
    config_patterns = ["BlueMap*", "Chunky*", "dcintergration*", "HuskHomes*", "Discord*", "ledger*", "LuckPerms*", "minimotd*", "tabtps*", "worldedit*", "do_a_barrel_roll-server*"]

    for pattern in mods_patterns:
        for file in glob.glob(f'./Minecraft/mods/{pattern}'):
            shutil.move(file, './temp/mods')

    for pattern in config_patterns:
        for file in glob.glob(f'./Minecraft/config/{pattern}'):
            shutil.move(file, './temp/config')

    # Delete the old mods folder and the config folder:
    logging.info('Deleting old mods and config folders')
    if os.path.exists('./Minecraft/mods'):
        os.system('rm -rf ./Minecraft/mods')
    if os.path.exists('./Minecraft/config'):
        os.system('rm -rf ./Minecraft/config')

    # Unzip the file if it's a zip file
    logging.info('Unzipping file')
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall('./Minecraft')

    # Move temp files back
    logging.info('Moving temp/mods and temp/config into Minecraft folder')
    shutil.move('./temp/mods', './Minecraft')
    shutil.move('./temp/config', './Minecraft')

    # Remove the zip file and the temp folder
    logging.info('Removing zip file and temp folder')
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists('./temp'):
        # remove folder and contents
        os.system('rm -rf ./temp')

# Main
app = Flask(__name__)

@app.route('/update', methods=['GET'])
def update():
    # Check if the correct API key was provided
    if request.args.get('api_key') == api_key:
        # Run the update script
        logging.info('Fetching latest server pack file ID')
        server_file_id = fetchServerPack()
        logging.info(f'Latest file ID: {server_file_id}')
        logging.info('Downloading...')
        file_path = fetchDownload(server_file_id)
        logging.info('Installing files')
        installFiles(file_path)
        logging.info('Sending Discord webhook')
        webhook = DiscordWebhook(url=discord_webhook, content='Server update complete ({server_file_id})')
        webhook.execute()
        logging.info('Update complete')
        return 'Update complete', 200
    else:
        return 'Invalid API key', 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)