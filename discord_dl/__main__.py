from src import DiscordDownloader, get_args

if __name__ == '__main__':
    args = get_args()
    dd = DiscordDownloader(args)
    dd.run()