import requests
import time
import os
from src.utils import download, extract_channel_ids, convert_discord_timestamp, mysleep, create_format_variables, create_filepath
from src.logger import logger

class DiscordDownloader():

    def __init__(self, options:dict) -> None:
        self.token = options.get('token', None)
        self.path = options.get('path', os.getcwd())
        self.file = options.get('file', None)
        self.channel_ids = options.get('channel_ids', [])
        self.message_count = options.get('message_count', -1)
        self.sleep = options.get('sleep', 0)
        self.sleep_random = options.get('sleep_random', [0,0])
        self.max_retries = options.get('max_retries', 10)
        self.date = options.get('date', None)
        self.date_before = options.get('date_before', None)
        self.date_after = options.get('date_after', None)
        self.username = options.get('username', [])
        self.user_id = options.get('user_id', [])
        self.channel_format = options.get('channel_format', 'downloads/{date:%Y-%m-%d}_{id}_{filename}.{ext}')
        self.dm_format = options.get('dm_format', 'downloads/{date:%Y-%m-%d}_{id}_{filename}.{ext}')
        self.windows_filenames = options.get('windows_filenames', False)
        self.restrict_filenames = options.get('restrict_filenames', False)
        self.simulate = options.get('simulate', False)

        if self.token == None:
            raise (f"No discord auth token passed")

        for key, value in options.items():
            if key == 'token':
                logger.debug(f"{key}: '**********'")
            else:
                logger.debug(f"{key}: {value}")

        if not os.path.exists(self.path):
            raise (f"Download path does not exist: {self.path}")
        
        self.channel_ids = extract_channel_ids(self.channel_ids)

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
            if self.message_count >= 0 and len(messages) >= self.message_count:
                logger.debug(f"Got {len(messages[:self.message_count])} messages for channel id {channel_id}")
                return self.find_messages(messages[:self.message_count])
            if len(messages_chunk) < 50:
                logger.debug(f"Got {len(messages)} messages for channel id {channel_id}")
                return self.find_messages(messages)
            mysleep(self.sleep, self.sleep_random)

    def retrieve_messages(self, session, channel_id:str, before_message_id:str=None) -> list:
        params = {'limit':50}
        if before_message_id:
            logger.info(f"Getting messages before message id {before_message_id} for channel id {channel_id}")
            params['before'] = before_message_id
        else:
            logger.info(f"Getting messages for channel id {channel_id}")
        retries = 0
        while retries < self.max_retries:
            try:
                messages = session.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', params=params).json()
            except ConnectionError:
                retries += 1
                sleep = 30 * retries
                logger.warning(f"{messages.status_code} Failed to get messages with url: {messages.url}")   
                logger.info(f"Sleeping for {sleep} seconds")
                time.sleep(sleep)
                logger.info(f"Retrying download {retries}/{self.max_retries}")
            else:
                return messages

    def find_messages(self, messages:list) -> list:
        filtered_data = []
        for message in messages:
            message_date = convert_discord_timestamp(message['timestamp']).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            if self.date and message_date != self.date:
                logger.debug(f"Message date {message_date:%Y-%m-%d} != args.date {self.date:%Y-%m-%d} for message id {message['id']}")
                continue
            if self.date_before and message_date >= self.date_before:
                logger.debug(f"Message date {message_date:%Y-%m-%d} >= args.date_before {self.date_before:%Y-%m-%d} for message id {message['id']}")
                continue
            if self.date_after and message_date <= self.date_after:
                logger.debug(f"Message date {message_date:%Y-%m-%d} <= args.date_after {self.date_after:%Y-%m-%d} for message id {message['id']}")
                continue
            if self.username and message['author']['username'] not in self.username:
                logger.debug(f"Message username {message['author']['username']} is not in args.username {self.username} for message id {message['id']}")
                continue
            if self.user_id and message['author']['id'] not in self.user_id:
                logger.debug(f"Message user id {message['author']['id']} is not in args.user_id {self.user_id} for message id {message['id']}")
                continue
            filtered_data.append(message)
        return filtered_data

    def download_attachment(self, attachment:dict, variables:dict) -> None:
        filepath = create_filepath(variables, self.path, self.channel_format, self.dm_format, self.windows_filenames, self.restrict_filenames)
        retries = 0
        while retries < self.max_retries:
            result = download(attachment['url'], filepath, self.simulate)
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
                logger.info(f"Retrying download {retries}/{self.max_retries}")
            else:
                break

    def run(self):
        headers = {'Authorization': self.token}
        session = requests.Session()
        session.headers.update(headers)
        for channel_id in self.channel_ids:
            channel_messages = self.get_all_messages(session, channel_id)
            channel_variables = self.get_channel_info(session, channel_id)
            for message in channel_messages:
                for attachment in message['attachments']:
                    if 'https://cdn.discordapp.com' == attachment['url'][:27]:
                        logger.warning(f"Attachment not hosted by discord {attachment['url']}")
                        continue
                    variables = {**create_format_variables(message, attachment), **channel_variables}
                    logger.debug(f"Format variables: {variables}")
                    self.download_attachment(attachment, variables)
                    mysleep(self.sleep, self.sleep_random)