import hashlib
import requests
import os
import time
import re
import random
from datetime import datetime
from src.logger import logger

def create_format_variables(message:dict, attachment:dict, index:int=0) -> dict:
    variables = {}
    filename, ext = os.path.splitext(attachment['filename'])
    variables['message_id'] = message['id']
    variables['id'] = attachment['id']
    variables['filename'] = filename
    variables['ext'] = ext[1:]
    variables['date'] = convert_discord_timestamp(message['timestamp'])
    variables['username'] = message['author']['username']
    variables['user_id'] = message['author']['id']
    return variables

def create_filepath(variables:dict, path:str, channel_format_template:str, dm_format_template:str, win_filenames:bool, restrict_filenames:bool) -> str:
    format_template = channel_format_template if 'server_id' in variables else dm_format_template
    components = []
    first = True
    while format_template:
        head, tail = os.path.split(format_template)
        if first:
            components.insert(0, sanitize_filename(tail.format(**variables), win_filenames, restrict_filenames))
            first = False
        else:
            components.insert(0, sanitize_foldername(tail.format(**variables), win_filenames, restrict_filenames))
        format_template = head
    components.insert(0, path)
    filepath = os.path.join(*components)
    return filepath  

def mysleep(sleep_base:int, sleep_range:list):
    if sleep_base or (sleep_range[0] != 0 and sleep_range[1] != 0):
        sleep = sleep_base + random.uniform(sleep_range[0], sleep_range[1])
        logger.info(f"Sleeping for {sleep} seconds")
        time.sleep(sleep)

def convert_discord_timestamp(timestamp):
    try:
        return datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%S%z")

def calculate_md5(file_path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def sanitize_filename(string, windows_naming, restrict_filenames):
    string = re.sub(r'[/]', '_', string)
    string = re.sub(r'[\x00-\x1f]', '', string)
    if os.name == 'nt' or windows_naming:
        string = re.sub(r'[<>:\"/\\\|\?\*]', '_', string)
    if restrict_filenames:
        string = re.sub(r'[^\x21-\x7f]', '_', string)
    return string

def sanitize_foldername(string, windows_naming, restrict_filenames):
    string = sanitize_filename(string, windows_naming, restrict_filenames)
    # windows folder names can not end with spaces (" ") or periods (".") 
    if os.name == 'nt' or windows_naming:
        string = string.strip(" .")
    return string

def extract_channel_ids(channel_ids):
    pattern = r"(\d+)|(https://discord.com/channels/[^/]+/(\d+))"
    results = []
    for channel_id in channel_ids:
        match = re.search(pattern, channel_id)
        if match:
            results.append(match.group(1) if match.group(1) else match.group(3))
        else:
            logger.warning(f'Could not find discord channel id in: {channel_id}')
    return results

def download(url:str, filepath:str, simulate=False) -> None:
    file_path, filename = os.path.split(filepath)
    logger.info(f"Downloading: {filename}")
    logger.debug(f"Path: {file_path}")
    logger.debug(f"URL: {url}")

    if not simulate:
        local_md5 = calculate_md5(filepath) if os.path.exists(filepath) else None
        with requests.get(url, stream=True) as r:
            if r.status_code != 200:
                return r.status_code
            server_md5 = r.headers.get('ETag', '')
            if not server_md5:
                logger.warning("No server hash found for attachment")
            if server_md5 == f'"{local_md5}"':
                return 1
            total = int(r.headers.get('content-length', 0))
            if not os.path.exists(file_path):
                logger.debug("Creating Path because it did not exist")
                os.makedirs(file_path)
            start = time.time()
            with open(filepath, 'wb') as f:
                bar_len = 0
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    downloaded += len(chunk) 
                    f.write(chunk)
                    bar_len = print_download_bar(total, downloaded, start, bar_len)
            print()
        return r.status_code
    start = time.time()
    print_download_bar(1, 1, start, 0)
    print()
    return 200

def calculate_bytes(bytes:str):
    if bytes/2**10 < 100:
        return (round(bytes/2**10, 1), 'KB')
    if bytes/2**20 < 100:
        return (round(bytes/2**20, 1), 'MB')
    if bytes/2**30 < 100:
        return (round(bytes/2**30, 1), 'GB')
    if bytes/2**40 < 100:
        return (round(bytes/2**40, 1), 'TB')    

def print_download_bar(total, downloaded, start, bar_len) -> None:
    td = time.time() - start
    td = 0.0000001 if td == 0 else td
    rate, rate_size = calculate_bytes((downloaded)/td)
    eta = time.strftime("%H:%M:%S", time.gmtime((total-downloaded) / rate))

    if total:
        done = int(50*downloaded/total)
        bar_fill = '='*done
        bar_empty = ' '*(50-done)
        total, size = calculate_bytes(total)
        downloaded, _ = calculate_bytes(downloaded)
    else:
        done = 50
        bar_fill = '?'*done
        bar_empty = ' '*(50-done)
        total = '???'
        downloaded, size = calculate_bytes(downloaded)
        eta = '??:??:??'

    progress_bar = f'[{bar_fill}{bar_empty}] {downloaded}/{total} {size} at {rate} {rate_size}/s ETA {eta}'
    overlap = bar_len - len(progress_bar)
    overlap_buffer = ' '*overlap if overlap > 0 else ''
    print(f'{progress_bar}{overlap_buffer}', end='\r')
    return len(progress_bar)