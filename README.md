# Discord Media Downloader

A python script that downloads media attachments from Discord server channels and direct messages.

## Getting Started

To get started, you will need to find your Discord Auth token. ***DO NOT*** share this token with anyone! ***DO NOT*** include your token when making a bug report! Anyone with this token can access your account.

## Usage

```bash
python discord_dl.py --token TOKEN [OPTIONS] [channel_id channel_url ...]
```

## Options

    --token                Your Discord Auth token, DO NOT SHARE IT
    --path                 The path where files will be downloaded to
    --channel-format       The format that attachments from server channels will be downloaded with
    --dm-format            The format that attachments from direct messages will be downloaded with
    --max-retries          The maximum number of times to attempt to download an attachment. Default is 0
    --filter-user-id       Only download attachments posted by this user id(s)
<!-- --sleep                The number of seconds to wait before attempting to download the next attachment. -->
<!-- --filter-username      The username of the user whose attachments you want to download. -->
<!-- --filter-date          Only download attachments posted on this date. -->
<!-- --filter-date-before   Only download attachments posted before this date. -->
<!-- --filter-date-after    Only download attachments posted after this date. -->


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
--dm-format "direct_messages/{username}_{user_id}/{date:%Y-%m-%d}_{id}_{filename}.{ext}"
```
## Examples

To download all attachments from a single channel, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path /path/to/download/folder channel_id
```

To download attachments from multiple channels, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path /path/to/download/folder channel_id_1 channel_id_2 channel_id_3
```

To download attachments from a channel posted by a specific user, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path /path/to/download/folder --filter-user-id USER_ID channel_id
```

<!-- To download attachments from a channel posted within a specific date range, run the following command:

```bash
python discord_dl.py --token YOUR_TOKEN --path /path/to/download/folder --filter-date-after 2020-01-01 --filter-date-before 2020-12-31 channel_id
``` -->
