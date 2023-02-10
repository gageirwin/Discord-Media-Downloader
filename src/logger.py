import logging
from src.arguments import get_args

args = get_args()
logger = logging.getLogger('discord_dl')

logging_level = logging.WARNING if args.quiet else logging.INFO
logging_level = logging.DEBUG if args.verbose else logging_level
logger.setLevel(logging_level)

formatter = logging.Formatter('%(levelname)s: %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)