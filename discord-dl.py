import requests
import time
import os
import hashlib
from myconfig import *

def calculate_md5(file_path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

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

def download_attachments(message:dict) -> None:
    author = message['author']['username']
    for attachment in message['attachments']:
        if 'https://cdn.discordapp.com' == attachment['url'][:27]:
            print("Warning attachment not hosted by discord skipping.")
            continue
        file_path = os.path.join(DOWNLOAD_PATH, author)
        file_name = f"{attachment['id']}_{attachment['filename']}"
        retries = 0
        while retries < MAX_RETRIES:
            result = download(attachment['url'], file_path, file_name)
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

def download(url:str, file_path:str, file_name:str) -> None:
    print(f"Downloading: {file_name}")
    print(f"url: {url}")
    # maybe just check file size instead oh md5 hash
    local_md5 = ''
    if os.path.exists(os.path.join(file_path, file_name)):
        local_md5 = calculate_md5(os.path.join(file_path, file_name))
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
        with open(os.path.join(file_path, file_name), 'wb') as f:
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
    if not AUTH_TOKEN:
        print('Set the AUTH_TOKEN variable in myconfig.py with your discord auth token.')
        quit()
    channel_ids = CHANNEL_IDS
    user_ids = USER_IDS
    headers = {'Authorization': AUTH_TOKEN}
    s = requests.Session()
    s.headers.update(headers)
    for channel_id in channel_ids:
        channel_messages = get_all_channel_messages(s, channel_id)
        if user_ids:
            channel_messages = filter_by_user_ids(user_ids, channel_messages)
        for message in channel_messages:
            download_attachments(message)

if __name__ == '__main__':
    main()
    print("Complete.")
