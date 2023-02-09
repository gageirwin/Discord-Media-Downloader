import requests
import time
import os
from datetime import datetime
from src.arguments import get_args
from src.helper import sanitize_filename, sanitize_foldername, download

class DiscordDownloader():

    def __init__(self, args) -> None:
        self.args = args
        # print(self.args.filter_by_username)

    def get_server_info(self, session, guild_id:str) -> dict:
        respose = session.get(f"https://discord.com/api/v9/guilds/{guild_id}").json()
        server_info = {
            'server_id':respose['id'],
            'server_name':respose['name'],
            'server_owner_id':respose['owner_id']
        }
        return server_info

    def get_channel_info(self, session, channel_id:str) -> dict:
        respose = session.get(f"https://discord.com/api/v9/channels/{channel_id}").json()
        channel_info = {'channel_id':respose['id']}
        # server channel
        if 'guild_id' in respose:
            channel_info['channel_name'] = respose['name']
            channel_info['channel_topic'] = respose['topic']
            server_info = self.get_server_info(session, respose['guild_id'])
            channel_info = {**channel_info, **server_info}
        return channel_info    

    def get_all_messages(self, session, channel_id:str) -> list:
        if self.args.message_count == 0:
            return []
        messages = self.retrieve_messages(session, channel_id, count=self.args.message_count)
        if len(messages) == 50 and len(messages) != self.args.message_count:
            while True:
                last_message_id = messages[-1]['id']
                more_messages = self.retrieve_messages(session, channel_id, count=self.args.message_count-len(messages), before_message_id=str(last_message_id))
                messages += more_messages
                if len(more_messages) < 50 or len(messages) == self.args.message_count:
                    break
        messages = self.filter_messages(messages)        
        return messages

    def retrieve_messages(self, session, channel_id:str, count=50, before_message_id:str=None) -> list:
        if count < 0 or count > 50:
            count = 50
        params = {'limit':count}
        if before_message_id:
            params['before'] = before_message_id
        messages = session.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', params=params).json()
        return messages

    def filter_messages(self, messages:list) -> list:
        filtered_messages = []
        for message in messages:
            if self.args.filter_by_user_id:
                if message['author']['id'] in self.args.filter_by_user_id:
                    if message not in filtered_messages:
                        filtered_messages.append(message)
            if self.args.filter_by_username:
                if message['author']['username'] in self.args.filter_by_username:
                    if message not in filtered_messages:
                        filtered_messages.append(message)                
        return filtered_messages

    def get_filepath(self, variables:dict):
        if 'server_id' in variables:
            path_template = self.args.channel_format
        else:
            path_template = self.args.dm_format
        components = []
        first = True
        while path_template:
            head, tail = os.path.split(path_template)
            if first:
                components.insert(0, sanitize_filename(tail.format(**variables), self.args.windows_filenames, self.args.restrict_filenames))
                first = False
            else:
                components.insert(0, sanitize_foldername(tail.format(**variables), self.args.windows_filenames, self.args.restrict_filenames))
            path_template = head
        components.insert(0, self.args.path)
        filepath = os.path.join(*components)
        return filepath  

    def download_attachments(self, message:dict, variables:dict) -> None:
        for attachment in message['attachments']:
            time.sleep(self.args.sleep)
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
            file_path = self.get_filepath(variables)
            retries = 0
            while retries < self.args.max_retries:
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

    def run(self):
        headers = {'Authorization': self.args.token}
        s = requests.Session()
        s.headers.update(headers)
        for channel_id in self.args.channel_ids:
            channel_messages = self.get_all_messages(s, channel_id)
            variables = self.get_channel_info(s, channel_id)
            for message in channel_messages:
                self.download_attachments(message, variables)

def main():
    args = get_args()
    dd = DiscordDownloader(args)
    dd.run()