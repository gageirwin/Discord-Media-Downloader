import requests
import time
import os
from datetime import datetime
from src.helper import sanitize_filename, sanitize_foldername, download, extract_channel_ids
from src.logger import logger

class DiscordDownloader():

    def __init__(self, args) -> None:
        self.args = args
        self.args.channel_ids = extract_channel_ids(args.channel_ids)
        for attr in vars(args):
            if attr == 'token':
                continue
            logger.debug(f"{attr}: {getattr(args, attr)}")

    def get_server_info(self, session, guild_id:str) -> dict:
        logger.info(f"Getting server info for server id {guild_id}")
        response = session.get(f"https://discord.com/api/v9/guilds/{guild_id}").json()
        server_info = {
            'server_id':response['id'],
            'server_name':response['name'],
            'server_owner_id':response['owner_id']
        }
        return server_info

    def get_channel_info(self, session, channel_id:str) -> dict:
        logger.info(f"Getting channel info for channel id {channel_id}")
        response = session.get(f"https://discord.com/api/v9/channels/{channel_id}").json()
        channel_info = {'channel_id':response['id']}
        # server channel
        if 'guild_id' in response:
            channel_info['channel_name'] = response['name']
            channel_info['channel_topic'] = response['topic']
            server_info = self.get_server_info(session, response['guild_id'])
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
                if len(messages) == self.args.message_count:
                    logger.debug(f"Found {len(messages)} messages for channel id {channel_id}")
                    break
                if len(more_messages) < 50:
                    logger.debug(f"Found {len(messages)} messages for channel id {channel_id}")
                    break
        messages = self.filter_messages(messages)        
        return messages

    def retrieve_messages(self, session, channel_id:str, count=50, before_message_id:str=None) -> list:
        count = count if 0 < count < 50 else 50
        params = {'limit':count}
        if before_message_id:
            logger.info(f"Getting {count} messages before message {before_message_id} for channel {channel_id}")
            params['before'] = before_message_id
        else:
            logger.info(f"Getting {count} messages for channel {channel_id}")
        messages = session.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', params=params).json()
        return messages

    def filter_messages(self, messages:list) -> list:
        filtered_messages = []
        for message in messages:
            if message['author']['id'] in self.args.filter_by_user_id:
                logger.debug(f"Filter found user id {message['author']['id']} for message id {message['id']}")
                filtered_messages.append(message)
                continue
            if message['author']['username'] in self.args.filter_by_username:
                logger.debug(f"Filter found username {message['author']['username']} for message id {message['id']}")
                filtered_messages.append(message)
                continue               
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
                logger.warning(f"Attachment not hosted by discord {attachment['url']}")
                continue
            filename, ext = os.path.splitext(attachment['filename'])
            variables['message_id'] = message['id']
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
                    logger.info('File already downloaded with matching hash and file name')
                    break
                elif result == 404:
                    logger.warning(f"{result} Failed to download url: {attachment['url']}")
                    break
                elif result != 200:
                    retries += 1
                    sleep = 30 * retries
                    logger.warning(f"{result} Failed to download url: {attachment['url']}")   
                    logger.info(f"Sleeping for {sleep} seconds")
                    time.sleep(sleep)
                    logger.info(f"Retrying download {retries}/10")
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