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
            - /analyzer/app/.env
        entrypoint: [ "dotnet", "/app/DiscordChatExporter.Cli.dll", "channels", "--guild", "<GUILD_ID>"]
"""

log_pattern = r"^.*\s(\d*) \| (.*)$"


def update_channels():
    with open("/analyzer/discord-output/guilds.json", "r", encoding='utf-8') as guilds:
        guilds_json = json.load(guilds)
        update_channel(guilds_json)


def update_channel(guilds_json):
    for guild in guilds_json["guilds"]:
        with open("channels/docker-compose-discord-channels.yml", "w", encoding='utf-8') as docker_compose:
            docker_compose.write(original_docker_compose.replace("<GUILD_ID>", str(guild["id"])))

        with open("/analyzer/tmp/channels.log", "a", encoding='utf-8') as output:
            subprocess.call("docker-compose -f channels/docker-compose-discord-channels.yml up", shell=True,
                            stdout=output)

        try:
            update_channels_json(str(guild["id"]))
        except Exception as e:
            clean_up(e, guild)
            try_again(guild)

        subprocess.call("docker-compose -f channels/docker-compose-discord-channels.yml down --remove-orphans",
                        shell=True)
        os.remove("/analyzer/tmp/channels.log")


def try_again(guild):
    try:
        update_channels_json(str(guild["id"]))
    except Exception as e:
        print("Failed after trying for second time", e)
        print("Skipping guild channels", guild["id"])


def clean_up(e, guild):
    print("Failed updating channels json ", e)
    print("Deleting channels.json and trying again")
    os.remove("/analyzer/discord-output/" + str(guild["id"]) + "/channels.json")


def update_channels_json(guild_id):
    with open("/analyzer/tmp/channels.log", "r", encoding='utf-8') as output:
        content = "\n".join(output.readlines())

        matches = re.finditer(log_pattern, content, re.MULTILINE)
        channel_list = []
        channel_list_duplicates = set()
        channels_json = {"channels": channel_list}

        channels_json, channel_list = fetch_existing(guild_id, channels_json, channel_list, channel_list_duplicates)
        update_existing(guild_id, channel_list, channel_list_duplicates, matches)
        dump_existing(guild_id, channels_json)


def dump_existing(guild_id, channels_json):
    with open("/analyzer/discord-output/" + guild_id + "/channels.json", "w", encoding='utf-8') as channels_output:
        json.dump(channels_json, channels_output)

    for channel in channels_json["channels"]:
        channel_path = "/analyzer/discord-output/" + guild_id + "/" + str(channel["id"])
        if not os.path.isfile(channel_path):
            print("Made dir " + channel_path + " as it didn't exist")
            os.mkdir(channel_path)


def update_existing(guild_id, channels_list, channels_list_duplicates, matches):
    for matchNum, match in enumerate(matches, start=1):
        if match.group(2) not in channels_list_duplicates:
            folder_path = "/analyzer/discord-output/" + guild_id + "/" + match.group(1)
            try:
                os.mkdir(folder_path)
                print("Making a folder as it didn't exist:", folder_path)
            except Exception as e:
                pass
            channels_list.append({"name": match.group(2), "id": int(match.group(1))})


def fetch_existing(guild_id, channels_json, channels_list, channels_list_duplicates):
    channel_path = "/analyzer/discord-output/" + guild_id + "/channels.json"
    if os.path.isfile(channel_path):
        with open(channel_path, "r", encoding='utf-8') as channels_existing:
            channels_json = json.load(channels_existing)
            channels_list = channels_json["channels"]
            for channel in channels_list:
                channels_list_duplicates.add(channel["name"])
    return channels_json, channels_list


if __name__ == '__main__':
    update_channels()
