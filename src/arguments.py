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

class LoadFileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        file_location = values
        if file_location:
            try:
                with open(file_location, 'r') as f:
                    lines = [line.strip() for line in f if not line.startswith('#')]
                    setattr(namespace, self.dest, lines)
            except FileNotFoundError:
                print(f"Warning: Could not find file at location '{file_location}'")
                setattr(namespace, self.dest, [])
        else:
            setattr(namespace, self.dest, [])

def extract_channel_ids(channel_ids):
    pattern = r"(\d+)|(https://discord.com/channels/[^/]+/(\d+))"
    results = []
    for channel_id in channel_ids:
        match = re.search(pattern, channel_id)
        if match:
            results.append(match.group(1) if match.group(1) else match.group(3))
        else:
            print(f'Warning could not find discord channel id in: {channel_id}')
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
        help='channel id or channel url',
        default=[]
    )

    parser.add_argument(
        '--file',
        type=str,
        help='File containing channel ids to download, one channel id per line. Lines starting with "#" are considered as comments and ignored',
        action=LoadFileAction,
        default=None
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
        default='{date:%Y-%m-%d}_{id}_{filename}.{ext}'
    )
    
    parser.add_argument(
        '--dm-format',
        type=str,
        help='The format that attachments from direct messages will be downloaded with',
        default='{date:%Y-%m-%d}_{id}_{filename}.{ext}'
    )

    parser.add_argument(
        '--restrict-filenames',
        type=bool,
        help='Restrict filenames to only ASCII characters and remove spaces',
        default=False
    )

    parser.add_argument(
        '--windows-filenames',
        type=bool,
        help='Force filenames to be Windows-compatible, filenames are Windows-compatible when using Windows',
        default=False
    )

    parser.add_argument(
        '--sleep',
        type=int,
        help='How long to sleep before attempting to download the next attachment, Default is 0',
        default=0
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        help='The maximum number of times to attempt to download an attachment, Default is 0',
        default=10
    )

    parser.add_argument(
        '--filter-by-user-id',
        type=str,
        help='Only download attachments posted by this user id(s)',
        action=ListAction,
        default=[]
    )

    parser.add_argument(
        '--filter-by-username',
        type=str,
        help='Only download attachments posted by this username(s) (Usernames are not unique! Usernames do not contain the #0000)',
        action=ListAction,
        default=[]
    )

    parser.add_argument(
        '--message-count',
        type=int,
        help='Only download attachments from the last # messages',
        default=-1
    )

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
    args.channel_ids += args.file if args.file is not None else []
    args.channel_ids = extract_channel_ids(args.channel_ids)
    return args