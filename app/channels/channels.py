import subprocess
import os
import re
import json

original_docker_compose = """
version: '3.4'

services:

    channels_fetcher:
        image: tyrrrz/discordchatexporter:2.25
        restart: "no"
        env_file:
            - /host/app/.env
        entrypoint: [ "dotnet", "/app/DiscordChatExporter.Cli.dll", "channels", "--guild", "<GUILD_ID>"]
"""

log_pattern = r"^.*\s(\d*) \| (.*)$"


def update_channels():
    with open("/host/output/guilds.json", "r", encoding='utf8') as guilds:
        guilds_json = json.load(guilds)
        update_channel(guilds_json)


def update_channel(guilds_json):
    for guild in guilds_json["guilds"]:
        with open("channels/docker-compose-discord-channels.yml", "w", encoding='utf8') as docker_compose:
            docker_compose.write(original_docker_compose.replace("<GUILD_ID>", str(guild["id"])))

        with open("/host/tmp/channels.log", "a", encoding='utf8') as output:
            subprocess.call("docker-compose -f channels/docker-compose-discord-channels.yml up", shell=True,
                            stdout=output)

        try:
            update_channels_json(str(guild["id"]))
        except Exception:
            os.remove("/host/output/" + str(guild["id"]) + "/channels.json")

        subprocess.call("docker-compose -f channels/docker-compose-discord-channels.yml down --remove-orphans",
                        shell=True)
        os.remove("/host/tmp/channels.log")


def update_channels_json(guild_id):
    with open("/host/tmp/channels.log", "r", encoding='utf8') as output:
        content = "\n".join(output.readlines())

        matches = re.finditer(log_pattern, content, re.MULTILINE)
        channel_list = []
        channel_list_duplicates = set()
        channels_json = {"channels": channel_list}

        channels_json, channel_list = fetch_existing(guild_id, channels_json, channel_list, channel_list_duplicates)
        update_existing(guild_id, channel_list, channel_list_duplicates, matches)
        dump_existing(guild_id, channels_json)


def dump_existing(guild_id, channelss_json):
    with open("/host/output/" + guild_id + "/channels.json", "w", encoding='utf8') as channels_output:
        json.dump(channelss_json, channels_output)


def update_existing(guild_id, channels_list, channels_list_duplicates, matches):
    for matchNum, match in enumerate(matches, start=1):
        if match.group(2) not in channels_list_duplicates:
            folder_path = "/host/output/" + guild_id + "/" + match.group(1)
            try:
                os.mkdir(folder_path)
                print("Making a folder as it didn't exist:", folder_path)
            except Exception:
                pass
            channels_list.append({"name": match.group(2), "id": int(match.group(1))})


def fetch_existing(guild_id, channels_json, channels_list, channels_list_duplicates):
    channel_path = "/host/output/" + guild_id + "/channels.json"
    if os.path.isfile(channel_path):
        with open(channel_path, "r", encoding='utf8') as channels_existing:
            channels_json = json.load(channels_existing)
            channels_list = channels_json["channels"]
            for channel in channels_list:
                channels_list_duplicates.add(channel["name"])
    return channels_json, channels_list


if __name__ == '__main__':
    update_channels()