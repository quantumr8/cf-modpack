import requests
import os
import zipfile
import logging
from pprint import pprint
import yaml
import hashlib

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the base URL and your API key
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)
base_url = config['base_api_url']
api_key = config['api_key']
project_id = config['project_id']


# Functions
def fetch_latest_fileid():
    headers = {'x-api-key': api_key}
    response = requests.get(f'{base_url}/mods/{project_id}', headers=headers)
    response.raise_for_status()  # Ensure we got a successful response
    data = response.json()
    logging.debug(pprint(data))
    logging.info(f'Server pack file ID: {data["data"]["serverPackFileId"]}')
    return data['data']['serverPackFileId']

def fetch_download(file_id):
    headers = {'x-api-key': api_key}
    response = requests.get(f'{base_url}/mods/{project_id}/files/{file_id}', headers=headers)
    response.raise_for_status()  # Ensure we got a successful response
    data = response.json()
    logging.debug(pprint(data))

    # Set variables from the API response
    download_url = data['downloadUrl']
    file_name = data['fileName']
    logging.info(f'Latest file date: {data["fileDate"]}')
    logging.info(f'Downloading file: {file_name} - {data["id"]}')
    response = requests.get(download_url)
    response.raise_for_status()

    # Save the file
    with open(file_name, 'wb') as f:
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
    return file_name

def installFiles(file_name):
    # Move files matching the regex to a temp folder
    logging.info('Moving files to temp folder')
    os.system(f'mkdir -p temp/mods')
    mods_regex = "(BlueMap.*)|(bmm.*)|(Chunky.*)|(dcintergration.*)|(HuskHomes.*)|(InvView.*)|(ledger.*)|(LuckPerms.*)|(minimotd.*)|(tabtps.*)|(worldedit.*)/gmi"
    config_regex = "(BlueMap.*)|(Chunky.*)|(dcintergration)|(HuskHomes)|(Discord.*)|(ledger)|(LuckPerms)|(minimotd)|(tabtps)|(worldedit)|(do_a_barrel_roll-server.*)/gmi"
    os.system(f'mv mods/{mods_regex} temp/mods')
    os.system(f'mv config/{config_regex} temp/config')

    # Delete the old mods folder and the config folder:
    logging.info('Deleting old mods and config folders')
    if os.path.exists('mods'):
        os.remove('mods')
    if os.path.exists('config'):
        os.remove('config')

    # Unzip the file if it's a zip file
    logging.info('Unzipping file')
    if file_name.endswith('.zip'):
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall('.')

    # Move the mods and config folders back
    logging.info('Moving my mods and config folders back')
    os.system(f'mv temp/mods mods')
    os.system(f'mv temp/config config')

    # Remove the zip file and the temp folder
    logging.info('Removing zip file and temp folder')
    if os.path.exists(file_name):
        os.remove(file_name)
    if os.path.exists('temp'):
        os.remove('temp')

# Main
logging.info('Fetching download')
file_name = fetch_download()
logging.info('Installing files')
# installFiles(file_name)
logging.info('Update complete')
