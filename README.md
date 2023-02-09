# Discord Media Downloader

A python script that downloads media attachments from Discord server channels and direct messages.

## Getting Started

To get started, you will need to find your Discord Auth token. ***DO NOT*** share this token with anyone! ***DO NOT*** include your token when making a bug report! Anyone with this token can access your account.

## Usage

```bash
python discord_dl.py --token TOKEN [OPTIONS] channel_id [channel_id ...]
```

## Options

    --token                 Your Discord Auth token, DO NOT SHARE IT
    --file                  File containing channel ids to download, one channel id per line. Lines starting with "#" are considered as comments and ignored
    --path                  The path where files will be downloaded to
    --channel-format        The format that attachments from server channels will be downloaded with
    --dm-format             The format that attachments from direct messages will be downloaded with
    --max-retries           The maximum number of times to attempt to download an attachment, Default is 0
    --sleep                 The number of seconds to wait before attempting to download the next attachment, Default is 0
    --restrict-filenames    Restrict filenames to only ASCII characters and remove spaces
    --windows-filenames     Force filenames to be Windows-compatible, filenames are Windows-compatible when using Windows
    --message-count         Only download attachments from the last # messages
    --filter-by-user-id     Only download attachments posted by this user id(s)
    --filter-username       Only download attachments posted by this username(s) (Usernames are not unique! Usernames do not contain the #0000)
<!-- --filter-date          Only download attachments posted on this date. -->
<!-- --filter-date-before   Only download attachments posted before this date. -->
<!-- --filter-date-after    Only download attachments posted after this date. -->

### Allowed Channel IDs 

`CHANEL_ID` will be a string of only numbers.

ID based:
```bash
"CHANNEL_ID"
```

URL based (server channel):
```bash
"https://discord.com/channels/SERVER_ID/CHANNEL_ID"
```

URL based (direct message):
```bash
"https://discord.com/channels/@me/CHANNEL_ID"
```

## Format Options

### General Options

- `{id}`                The attachment id
- `{filename}`          The attachment file name
- `{ext}`               The attachment file extension
- `{date}`              The message post date. [strftime()-style formatting options](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) are supported.
- `{channel_id}`        The channel id
- `{username}`          The username of the message author
- `{user_id}`           The id of the message author

### Sever Channel Specific Options

- `{channel_name}`      The name of the channel
- `{channel_topic}`     The channel topic
- `{server_id}`         The server id
- `{server_name}`       The server name
- `{server_owner_id}`   The id of th owner of the server

###  Defaults
```bash
--path "CURRENT_WORKING_DIRECTORY/downloads"
```
```bash    
--channel-format "servers/{server_name}_{server_id}/{channel_name}_{channel_id}/{username}_{user_id}/{date:%Y-%m-%d}_{id}_{filename}.{ext}"
```
```bash
--dm-format "direct_messages/{username}_{channel_id}/{username}_{user_id}/{date:%Y-%m-%d}_{id}_{filename}.{ext}"
```
## Examples

To download all attachments from a single channel, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path "/path/to/download/folder" "channel_id"
```

To download attachments from multiple channels, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path "/path/to/download/folder" "channel_id_1" "channel_id_2" "channel_id_3"
```

To download attachments from a channel posted by a specific user, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path "/path/to/download/folder" --filter-user-id USER_ID "channel_id"
```

To download attachments from a direct message, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path /path/to/download/folder "https://discord.com/channels/@me/channel_id"
```

<!-- To download attachments from a channel posted within a specific date range, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path /path/to/download/folder --filter-date-after 2020-01-01 --filter-date-before 2020-12-31 channel_id
``` -->

## Warnings

This probably breaks Discords terms of service and you might get banned etc ...  
Use and alt account? 🤷‍♂️