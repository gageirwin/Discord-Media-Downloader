import hashlib
import requests
import os
import time
import re

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
