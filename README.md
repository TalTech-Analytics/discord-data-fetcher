## Discord

Script which fetches all messages from all guilds visible when ran docker-compose-discord.yml

## Sample output

- <GUILD_ID_1>
  - <CHANNEL_ID_1>
    - channel.json
  - <CHANNEL_ID_2>
  - <CHANNEL_ID_3>
  - channels.json
- <GUILD_ID_2>
- <GUILD_ID_3>
- guilds.json

And writes it to output. If given input has invalid structure then given file will be ignored

## Running locally

Run `docker-compose -f docker-compose-discord.yml up`

## When developing

- Comment out line 3 in `Dockerfile-discord`
- Add all mounts from `docker-compose-discord.yml` to `docker-compose-build-discord.yml`
- create .env file from ..env with your token
- Run `docker-compose -f docker-compose-build-discord.yml up --build`
