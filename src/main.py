import requests
import time
import os
import random
from src.utils import sanitize_filename, sanitize_foldername, download, extract_channel_ids, convert_discord_timestamp
from src.logger import logger

class DiscordDownloader():

    def __init__(self, args) -> None:
        self.args = args
        self.args.channel_ids = extract_channel_ids(args.channel_ids)
        for attr in vars(args):
            if attr == 'token':
                continue
            logger.debug(f"{attr}: {getattr(args, attr)}")
        if not os.path.exists(self.args.path):
            logger.error(f"--path does not exist: {self.args.path}")
            exit()

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
        messages = []
        last_message_id = None
        while True:
            messages_chunk = self.retrieve_messages(session, channel_id, before_message_id=last_message_id)
            messages += messages_chunk
            last_message_id = messages_chunk[-1]['id']
            if self.args.message_count >= 0 and len(messages) >= self.args.message_count:
                logger.debug(f"Got {len(messages[:self.args.message_count])} messages for channel id {channel_id}")
                return self.find_messages(messages[:self.args.message_count])
            if len(messages_chunk) < 50:
                logger.debug(f"Got {len(messages)} messages for channel id {channel_id}")
                return self.find_messages(messages)
            if self.args.sleep or (self.args.sleep_random[0] != 0 and self.args.sleep_random[1] != 0):
                sleep = self.args.sleep + random.uniform(self.args.sleep_random[0], self.args.sleep_random[1])
                logger.info(f"Sleeping for {sleep} seconds")
                time.sleep(sleep)

    def retrieve_messages(self, session, channel_id:str, before_message_id:str=None) -> list:
        params = {'limit':50}
        if before_message_id:
            logger.info(f"Getting messages before message id {before_message_id} for channel id {channel_id}")
            params['before'] = before_message_id
        else:
            logger.info(f"Getting messages for channel id {channel_id}")
        messages = session.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', params=params).json()
        return messages

    def find_messages(self, messages:list) -> list:
        filtered_data = []
        for message in messages:
            message_date = convert_discord_timestamp(message['timestamp']).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            if self.args.date and message_date != self.args.date:
                logger.debug(f"Message date {message_date:%Y-%m-%d} != args.date {self.args.date:%Y-%m-%d} for message id {message['id']}")
                continue
            if self.args.date_before and message_date >= self.args.date_before:
                logger.debug(f"Message date {message_date:%Y-%m-%d} >= args.date_before {self.args.date_before:%Y-%m-%d} for message id {message['id']}")
                continue
            if self.args.date_after and message_date <= self.args.date_after:
                logger.debug(f"Message date {message_date:%Y-%m-%d} <= args.date_after {self.args.date_after:%Y-%m-%d} for message id {message['id']}")
                continue
            if self.args.username and message['author']['username'] not in self.args.username:
                logger.debug(f"Message username {message['author']['username']} is not in args.username {self.args.username} for message id {message['id']}")
                continue
            if self.args.user_id and message['author']['id'] not in self.args.user_id:
                logger.debug(f"Message user id {message['author']['id']} is not in args.user_id {self.args.user_id} for message id {message['id']}")
                continue
            filtered_data.append(message)
        return filtered_data

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
            if 'https://cdn.discordapp.com' == attachment['url'][:27]:
                logger.warning(f"Attachment not hosted by discord {attachment['url']}")
                continue
            filename, ext = os.path.splitext(attachment['filename'])
            variables['message_id'] = message['id']
            variables['id'] = attachment['id']
            variables['filename'] = filename
            variables['ext'] = ext[1:]
            variables['date'] = convert_discord_timestamp(message['timestamp'])
            variables['username'] = message['author']['username']
            variables['user_id'] = message['author']['id']
            file_path = self.get_filepath(variables)
            retries = 0
            while retries < self.args.max_retries:
                result = download(attachment['url'], file_path, self.args.simulate)
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
            if self.args.sleep or (self.args.sleep_random[0] != 0 and self.args.sleep_random[1] != 0):
                sleep = self.args.sleep + random.uniform(self.args.sleep_random[0], self.args.sleep_random[1])
                logger.info(f"Sleeping for {sleep} seconds")
                time.sleep(sleep)

    def run(self):
        headers = {'Authorization': self.args.token}
        s = requests.Session()
        s.headers.update(headers)
        for channel_id in self.args.channel_ids:
            channel_messages = self.get_all_messages(s, channel_id)
            variables = self.get_channel_info(s, channel_id)
            for message in channel_messages:
                self.download_attachments(message, variables)