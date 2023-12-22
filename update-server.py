import requests
import os
import zipfile
import logging
from pprint import pprint
import yaml
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set the base URL and your API key
with open('./updater-config.yaml', 'r') as f:
    config = yaml.safe_load(f)
base_url = config['base_api_url']
api_key = config['api_key']
project_id = config['project_id']


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

    # Save the file
    file_path = os.path.join('./Minecraft', file_name)
    with open(file_path, 'wb') as f:
        f.write(response.content)
    logging.info(f'Downloaded {file_name} from {download_url}')

    # Test the file hash with sha1
    file_hash = data['hashes'][0]['value']
    sha1 = hashlib.sha1()
    try:
        with open(file_name, 'rb') as file:
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
        if os.path.exists(file_name):
            os.remove(file_name)
        exit()
    return file_path

def installFiles(file_path):
    # Move files matching the regex to a temp folder
    logging.info('Moving files to temp folder')
    os.system(f'mkdir -p ./temp/mods')
    mods_regex = "(BlueMap.*)|(bmm.*)|(Chunky.*)|(dcintergration.*)|(HuskHomes.*)|(InvView.*)|(ledger.*)|(LuckPerms.*)|(minimotd.*)|(tabtps.*)|(worldedit.*)/gmi"
    config_regex = "(BlueMap.*)|(Chunky.*)|(dcintergration)|(HuskHomes)|(Discord.*)|(ledger)|(LuckPerms)|(minimotd)|(tabtps)|(worldedit)|(do_a_barrel_roll-server.*)/gmi"
    os.system(f'mv ./Minecraft/mods/{mods_regex} ./temp/mods')
    os.system(f'mv ./Minecraft/config/{config_regex} ./temp/config')

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

    # Move the mods and config folders back
    logging.info('Moving my mods and config folders back')
    os.system(f'mv ./temp/mods mods')
    os.system(f'mv ./temp/config config')

    # Remove the zip file and the temp folder
    logging.info('Removing zip file and temp folder')
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists('./temp'):
        # remove folder and contents
        os.system('rm -rf ./temp')

# Main
logging.info('Fetching latest server pack file ID')
server_file_id = fetchServerPack()
logging.info(f'Latest file ID: {server_file_id}')
logging.info('Downloading...')
file_path = fetchDownload(server_file_id)
logging.info('Installing files')
installFiles(file_path)
logging.info('Update complete')
