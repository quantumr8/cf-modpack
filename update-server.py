import requests
import os
import zipfile
import logging

# Set the base URL and your API key
base_url = 'https://addons-ecs.forgesvc.net/api/v2'
api_key = '$2a$10$n/7BgMofPnif6zZfqPKuW..m9rcrI/wlL4a2WxJEp3f2AXwupXXom'
project_id = '466901'

# Get the latest file download URL from the CurseForge API
headers = {'x-api-key': api_key}
response = requests.get(f'{base_url}/addon/{project_id}/files', headers=headers)
response.raise_for_status()  # Ensure we got a successful response
data = response.json()

# Sort the data by file date, get the latest file
latest_file = sorted(data, key=lambda x: x['fileDate'], reverse=True)[0]
logging.info(f'Latest file: {latest_file}')

# Download the file
download_url = latest_file['downloadUrl']
file_name = latest_file['fileName']
response = requests.get(download_url)
response.raise_for_status()
logging.info(f'Downloading {file_name} from {download_url}')

# Save the file
with open(file_name, 'wb') as f:
    f.write(response.content)

# Move files matching the regex to a temp folder
logging.info('Moving files to temp folder')
logging.info('simulating moving files and unzipping') # Debugging
os.system('sleep 5') # Debugging: simulate moving files and unzipping
# Debugging: commented out the below
# os.system(f'mkdir -p temp/mods')
# mods_regex = "(BlueMap.*)|(bmm.*)|(Chunky.*)|(dcintergration.*)|(HuskHomes.*)|(InvView.*)|(ledger.*)|(LuckPerms.*)|(minimotd.*)|(tabtps.*)|(worldedit.*)/gmi"
# config_regex = "(BlueMap.*)|(Chunky.*)|(dcintergration)|(HuskHomes)|(Discord.*)|(ledger)|(LuckPerms)|(minimotd)|(tabtps)|(worldedit)|(do_a_barrel_roll-server.*)/gmi"
# os.system(f'mv mods/{mods_regex} temp/mods')
# os.system(f'mv config/{config_regex} temp/config')

# # Delete the old mods folder and the config folder:
# logging.info('Deleting old mods and config folders')
# if os.path.exists('mods'):
#     os.remove('mods')
# if os.path.exists('config'):
#     os.remove('config')

# # Unzip the file if it's a zip file
# logging.info('Unzipping file')
# if file_name.endswith('.zip'):
#     with zipfile.ZipFile(file_name, 'r') as zip_ref:
#         zip_ref.extractall('.')

# # Move the mods and config folders back
# logging.info('Moving my mods and config folders back')
# os.system(f'mv temp/mods mods')
# os.system(f'mv temp/config config')

# # Remove the zip file and the temp folder
# logging.info('Removing zip file and temp folder')
# if os.path.exists(file_name):
#     os.remove(file_name)
# if os.path.exists('temp'):
#     os.remove('temp')

logging.info('Update complete')
