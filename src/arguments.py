import argparse
import os
import re
from datetime import datetime

class ListAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, [val for val in values.split(',')])

class DateAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        date = datetime.strptime(values, r'%Y-%m-%d')
        setattr(args, self.dest, date)

def extract_channel_ids(channel_ids):
    pattern = r"(\d+)|(https://discord.com/channels/[^/]+/(\d+))"
    results = []
    for channel_id in channel_ids:
        match = re.search(pattern, channel_id)
        if match:
            results.append(match.group(1) if match.group(1) else match.group(3))
    return results

def get_args():
    parser = argparse.ArgumentParser(description='Download discord media attachments')

    # Add an argument with the option "-n" or "--name"
    parser.add_argument(
        '--token',
        type=str,
        help='Your Discord Auth token, DO NOT SHARE IT',
        required=True
    )

    parser.add_argument(
        'channel_ids',
        type=str,
        nargs='*',
        help='channel id or channel url'
    )

    parser.add_argument(
        '--path',
        type=str,
        help='The path where files will be downloaded to',
        default=os.path.join(os.getcwd(), 'downloads')
    )

    parser.add_argument(
        '--channel-format',
        type=str,
        help='The format that attachments from server channels will be downloaded with',
        default='servers/{server_name}_{server_id}/{channel_name}_{channel_id}/{username}_{user_id}/{date:%Y-%m-%d}_{id}_{filename}.{ext}'
    )
    
    parser.add_argument(
        '--dm-format',
        type=str,
        help='The format that attachments from direct messages will be downloaded with',
        default='direct_messages/{username}_{user_id}/{date:%Y-%m-%d}_{id}_{filename}.{ext}'
    )

    # parser.add_argument(
    #     '--sleep',
    #     type=int,
    #     help='How long to sleep before attempting to download the next attachment',
    #     default=0
    # )

    parser.add_argument(
        '--max-retries',
        type=int,
        help='The maximum number of times to attempt to download an attachment, Default is 0',
        default=10
    )

    parser.add_argument(
        '--filter-user-id',
        type=str,
        help='Only download attachments posted by this user id(s)',
        action=ListAction,
        default=[]
    )

    # parser.add_argument(
    #     '--filter-username',
    #     type=str,
    #     help='Only download attachments posted by this username (Usernames are not unique and do not contain the #0000)',
    #     action=ListAction,
    #     default=[]
    # )

    # parser.add_argument(
    #     '--filter-date',
    #     type=str,
    #     action=DateAction,
    #     help='Only download attachments posted at this date',
    # )

    # parser.add_argument(
    #     '--filter-date-before',
    #     type=str,
    #     action=DateAction,
    #     help='Only download attachments posted before this date',
    # )

    # parser.add_argument(
    #     '--filter-date-after',
    #     type=str,
    #     action=DateAction,
    #     help='Only download attachments posted after this date',
    # )

    # Parse the arguments passed in the command-line
    args = parser.parse_args()
    args.channel_ids = extract_channel_ids(args.channel_ids)
    return args