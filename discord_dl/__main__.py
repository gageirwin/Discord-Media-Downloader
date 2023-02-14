from src import DiscordDownloader, get_args

if __name__ == '__main__':
    options = vars(get_args())
    dd = DiscordDownloader(options)
    dd.run()