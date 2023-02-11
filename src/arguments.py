import argparse
import os
from datetime import datetime

class ListAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        setattr(args, self.dest, [val for val in values.split(',')])

class DateAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        date = datetime.strptime(values, r'%Y%m%d')
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

def get_args():
    parser = argparse.ArgumentParser(description='Download discord media attachments')

    parser.add_argument(
        '--token',
        type=str,
        help='Your Discord Auth token, DO NOT SHARE IT',
        required=True
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Set logging level to DEBUG',
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Set logging level to WARNING',
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
        help='The path where files will be downloaded to. Path must exist and can not use format variables',
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
        help='How long to sleep in between downloading attachments and retrieving messages, Default is 0',
        default=0
    )

    parser.add_argument(
        '--sleep-random',
        type=int,
        nargs=2,
        help='Set a random range from A to B to sleep in between downloading attachments and retrieving messages, If using --sleep the random time will be added on',
        default=[0, 0]
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        help='The maximum number of times to attempt to download an attachment, Default is 0',
        default=10
    )

    parser.add_argument(
        '--user-id',
        type=str,
        help='Only download attachments posted by this user id(s)',
        action=ListAction,
        default=[]
    )

    parser.add_argument(
        '--username',
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

    parser.add_argument(
        '--date',
        type=str,
        action=DateAction,
        help='Only download attachments from messages posted at this date in YYYYMMDD format',
        default=None
    )

    parser.add_argument(
        '--date-before',
        type=str,
        action=DateAction,
        help='Only download attachments from messages posted before this date in YYYYMMDD format',
        default=None
    )

    parser.add_argument(
        '--date-after',
        type=str,
        action=DateAction,
        help='Only download attachments from messages posted after this date in YYYYMMDD format',
        default=None
    )

    parser.add_argument(
        '--simulate',
        action='store_true',
        help='Do not write to disc',
    )

    # Parse the arguments passed in the command-line
    args = parser.parse_args()
    args.channel_ids += args.file if args.file is not None else []


    return args