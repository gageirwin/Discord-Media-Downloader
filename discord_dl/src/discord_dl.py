import requests
import time
import os
from src.utils import download, extract_channel_ids, convert_discord_timestamp, mysleep, create_format_variables, create_filepath
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
            mysleep(self.args.sleep, self.args.sleep_random)

    def retrieve_messages(self, session, channel_id:str, before_message_id:str=None) -> list:
        params = {'limit':50}
        if before_message_id:
            logger.info(f"Getting messages before message id {before_message_id} for channel id {channel_id}")
            params['before'] = before_message_id
        else:
            logger.info(f"Getting messages for channel id {channel_id}")
        retries = 0
        while retries < self.args.max_retries:
            try:
                messages = session.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', params=params).json()
            except ConnectionError:
                retries += 1
                sleep = 30 * retries
                logger.warning(f"{messages.status_code} Failed to get messages with url: {messages.url}")   
                logger.info(f"Sleeping for {sleep} seconds")
                time.sleep(sleep)
                logger.info(f"Retrying download {retries}/{self.args.max_retries}")
            else:
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

    def download_attachment(self, attachment:dict, variables:dict) -> None:
        filepath = create_filepath(variables, self.args.path, self.args.channel_format, self.args.dm_format, self.args.windows_filenames, self.args.restrict_filenames)
        retries = 0
        while retries < self.args.max_retries:
            result = download(attachment['url'], filepath, self.args.simulate)
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
                logger.info(f"Retrying download {retries}/{self.args.max_retries}")
            else:
                break

    def run(self):
        headers = {'Authorization': self.args.token}
        session = requests.Session()
        session.headers.update(headers)
        for channel_id in self.args.channel_ids:
            channel_messages = self.get_all_messages(session, channel_id)
            variables = self.get_channel_info(session, channel_id)
            for message in channel_messages:
                for attachment in message['attachments']:
                    if 'https://cdn.discordapp.com' == attachment['url'][:27]:
                        logger.warning(f"Attachment not hosted by discord {attachment['url']}")
                        continue
                    variables = {**create_format_variables(message, attachment), **variables}
                    self.download_attachment(attachment, variables)
                    mysleep(self.args.sleep, self.args.sleep_random)