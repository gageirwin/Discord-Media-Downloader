from src.main import DiscordDownloader
from src.arguments import get_args

if __name__ == '__main__':
    args = get_args()
    dd = DiscordDownloader(args)
    dd.run()