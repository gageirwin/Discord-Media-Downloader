import requests
import time
import os
import hashlib
from datetime import datetime
from src.arguments import get_args

def calculate_md5(file_path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_server_info(session, guild_id:str) -> dict:
    respose = session.get(f"https://discord.com/api/v9/guilds/{guild_id}").json()
    server_info = {
        'server_id':respose['id'],
        'server_name':respose['name'],
        'server_owner_id':respose['owner_id']
    }
    return server_info

def get_channel_info(session, channel_id:str) -> dict:
    respose = session.get(f"https://discord.com/api/v9/channels/{channel_id}").json()
    channel_info = {'channel_id':respose['id']}
    # server channel
    if 'guild_id' in respose:
        channel_info['channel_name'] = respose['name']
        channel_info['channel_topic'] = respose['topic']
        server_info = get_server_info(session, respose['guild_id'])
        channel_info = {**channel_info, **server_info}
    return channel_info    

def get_all_channel_messages(session, channel_id:str) -> list:
    channel_messages = retrieve_messages(session, channel_id)
    if len(channel_messages) < 50:
        return channel_messages
    while True:
        last_message_id = channel_messages[-1]['id']
        more_channel_messages = retrieve_messages(session, channel_id, before_message_id=str(last_message_id))
        channel_messages += more_channel_messages
        if len(more_channel_messages) < 50:
            break
    return channel_messages

def retrieve_messages(session, channel_id:str, before_message_id:str=None) -> list:
    params = {'limit':'50'}
    if before_message_id:
        params['before'] = before_message_id
    return session.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', params=params).json()

def filter_by_user_ids(user_ids:list, messages:list) -> list:
    filtered_messages = []
    for message in messages:
        if message['author']['id'] in user_ids:
            filtered_messages.append(message)
    return filtered_messages

def sanities_string(string:str):
    return string

def construct_filepath(variables:dict, args):
    if 'server_id' in variables:
        path_template = args.channel_format
    else:
        path_template = args.dm_format
    components = []
    while path_template:
        head, tail = os.path.split(path_template)
        components.insert(0, sanities_string(tail.format(**variables)))
        path_template = head
    components.insert(0, args.path)
    filepath = os.path.join(*components)
    return filepath  

def download_attachments(message:dict, variables:dict, args) -> None:
    for attachment in message['attachments']:
        if 'https://cdn.discordapp.com' == attachment['url'][:27]:
            print("Warning attachment not hosted by discord skipping.")
            continue
        filename, ext = os.path.splitext(attachment['filename'])
        variables['id'] = attachment['id']
        variables['filename'] = filename
        variables['ext'] = ext[1:]
        variables['date'] = datetime.strptime(message['timestamp'], r"%Y-%m-%dT%H:%M:%S.%f%z")
        variables['username'] = message['author']['username']
        variables['user_id'] = message['author']['id']
        file_path = construct_filepath(variables, args)
        retries = 0
        while retries < args.max_retries:
            result = download(attachment['url'], file_path)
            if result == 1:
                print('File already downloaded')
                break
            elif result == 404:
                print(f"Failed to download error {result}")
                break
            elif result != 200:
                retries += 1
                sleep = 30 * retries
                print(f"Failed to download error {result} sleeping for {sleep} seconds")
                time.sleep(sleep)
                print(f"Retrying download {retries}/10")
            else:
                break

def download(url:str, filepath:str) -> None:
    file_path, filename = os.path.split(filepath)
    print(f"Downloading: {filename}")
    print(f"url: {url}")
    # maybe just check file size instead oh md5 hash
    local_md5 = ''
    if os.path.exists(filepath):
        local_md5 = calculate_md5(filepath)
    with requests.get(url, stream=True) as r:
        if r.status_code != 200:
            return r.status_code
        server_md5 = r.headers.get('ETag', '_')
        if server_md5 == '_':
            print("Warning no server hash found for attachment")
        elif server_md5 == f'"{local_md5}"':
            return 1
        total = int(r.headers.get('content-length', 0))
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        with open(filepath, 'wb') as f:
            start = time.time()
            bar_len = 0
            downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                downloaded += len(chunk) 
                f.write(chunk)
                bar_len = print_download_bar(total, downloaded, start, bar_len)
        print()
        return r.status_code

def print_download_bar(total, downloaded, start, bar_len) -> None:
    td = time.time() - start
    
    if td == 0:
        rate = 0
        eta = "00:00:00"
    else:
        rate = (downloaded)/td
        eta = time.strftime("%H:%M:%S", time.gmtime((total-downloaded) / rate))

    if rate/2**10 < 100:
        rate = (round(rate/2**10, 1), 'KB')
    elif rate/2**20 < 100:
        rate = (round(rate/2**20, 1), 'MB')
    else:
        rate = (round(rate/2**30, 1), 'GB')

    if total:
        done = int(50*downloaded/total)
        bar_fill = '='*done
        bar_empty = ' '*(50-done)
        if total/2**10 < 100:
            total = (round(total/2**10, 1), 'KB')
            downloaded = round(downloaded/2**10,1)
        elif total/2**20 < 100:
            total = (round(total/2**20, 1), 'MB')
            downloaded = round(downloaded/2**20,1)
        else:
            total = (round(total/2**30, 1), 'GB')
            downloaded = round(downloaded/2**30,1)
    else:
        done = 50
        bar_fill = '?'*done
        bar_empty = ' '*(50-done)
        if downloaded/2**10 < 100:
            total = ('???', 'KB')
            downloaded = round(downloaded/2**10,1)
        elif downloaded/2**20 < 100:
            total = ('???', 'MB')
            downloaded = round(downloaded/2**20,1)
        else:
            total = ('???', 'GB')
            downloaded = round(downloaded/2**30,1)

    progress_bar = f'[{bar_fill}{bar_empty}] {downloaded}/{total[0]} {total[1]} at {rate[0]} {rate[1]}/s ETA {eta}'
    overlap = bar_len - len(progress_bar)
    overlap_buffer = ' '*overlap if overlap > 0 else ''
    print(f'{progress_bar}{overlap_buffer}', end='\r')
    return len(progress_bar)  

def main():
    args = get_args()
    channel_ids = args.channel_ids
    user_ids = args.filter_user_id
    headers = {'Authorization': args.token}
    s = requests.Session()
    s.headers.update(headers)
    for channel_id in channel_ids:
        channel_messages = get_all_channel_messages(s, channel_id)
        if user_ids:
            channel_messages = filter_by_user_ids(user_ids, channel_messages)
        variables = get_channel_info(s, channel_id)
        for message in channel_messages:
            download_attachments(message, variables, args)