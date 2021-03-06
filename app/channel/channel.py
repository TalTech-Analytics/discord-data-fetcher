import subprocess
import json
import shutil
import os
import dateutil.parser
from datetime import timedelta

original_docker_compose = """
version: '3.4'

services:

    chat_exporter:
        image: tyrrrz/discordchatexporter:stable
        restart: "no"
        privileged: "true"
        env_file:
            - /analyzer/app/.env
        environment:
            GUILDID: <GUILD_ID>
        entrypoint: [ "dotnet", "/app/DiscordChatExporter.Cli.dll", "export", "--channel", "<CHANNEL_ID>", "--after", "<AFTER>", "-f", "Json" ]
        volumes:
            - /analyzer/discord-output/<GUILD_ID>/<CHANNEL_ID>/:/app/out/
"""


def update_all_messages():
    with open("/analyzer/discord-output/guilds.json", "r", encoding='utf-8') as guilds:
        guilds_json = json.load(guilds)
        for guild in guilds_json["guilds"]:
            update_guild_messages(str(guild['id']))


def update_guild_messages(guild_id):
    with open("/analyzer/discord-output/" + guild_id + "/channels.json", "r", encoding='utf-8') as channels:
        channels_json = json.load(channels)
        print("Updating channels:", [x["name"] for x in channels_json["channels"]])
        for channel in channels_json["channels"]:
            try:
                update_channel(guild_id, str(channel["id"]))
            except Exception as e:
                clean_up(channel, e, guild_id)
                try_again(channel, guild_id)


def clean_up(channel, e, guild_id):
    print("Failed updating guild:", guild_id, "channel:", str(channel["id"]), "time:", e)
    folder_path = "/analyzer/discord-output/" + guild_id + "/" + str(channel["id"]) + "/"
    print("Deleting channel:", folder_path)
    shutil.rmtree(folder_path)


def try_again(channel, guild_id):
    print("Trying again")
    try:
        update_channel(guild_id, str(channel["id"]))
    except Exception as e:
        print("Failed updating guild:", guild_id, "channel:", str(channel["id"]), "second time:", e)
        print("Skipping")


def update_channel(guild_id, channel_id):
    folder_path = "/analyzer/discord-output/" + guild_id + "/" + channel_id + "/"
    after = get_latest_timestamp(folder_path)
    print("Fetching all messages after:", after)
    docker_compose_file = original_docker_compose \
        .replace("<GUILD_ID>", guild_id) \
        .replace("<CHANNEL_ID>", channel_id) \
        .replace("<AFTER>", after)

    with open(folder_path + "docker-compose-discord-channel.yml", "w", encoding='utf-8') as docker_compose:
        docker_compose.write(docker_compose_file)

    subprocess.call("docker-compose -f " + folder_path + "docker-compose-discord-channel.yml up", shell=True)
    subprocess.call("docker-compose -f " + folder_path + "docker-compose-discord-channel.yml down --remove-orphans",
                    shell=True)

    os.remove(folder_path + "docker-compose-discord-channel.yml")

    if os.path.isfile(folder_path + "channel.json"):
        print("Updating existing", folder_path)
        update_existing_messages(channel_id, folder_path)
    else:
        print("Creating new", folder_path)
        create_new_messages(channel_id, folder_path)


def get_latest_timestamp(folder_path):
    after = None
    if os.path.isfile(folder_path + "channel.json"):
        with open(folder_path + "channel.json", "r", encoding='utf-8') as channel_existing:
            channel_json = json.load(channel_existing)
            for message in channel_json["messages"]:
                insertion_date = dateutil.parser.parse(message["timestamp"])
                if after is None or insertion_date > after:
                    after = insertion_date
        if after is None:
            after = ""
        else:
            after = (after.date() - timedelta(days=1)).isoformat()
    else:
        print("No channel.json. Getting all messages")
        after = ""
    return after


def create_new_messages(channel_id, folder_path):
    for filename in os.listdir(folder_path):
        print("Found file:", filename)
        if channel_id in filename:
            print("Renamed it to channel.json")
            os.rename(folder_path + filename, folder_path + "channel.json")


def update_existing_messages(channel_id, folder_path):
    existing_messages = set()

    with open(folder_path + "channel.json", "r", encoding='utf-8') as channel_existing:
        print("Reading channel.json")
        channel_json = json.load(channel_existing)
        for message in channel_json["messages"]:
            existing_messages.add(message["id"])

    for filename in os.listdir(folder_path):
        if channel_id in filename:
            print("Found new file", filename)

            with open(folder_path + filename, "r", encoding='utf-8') as append:
                print("Appending ", filename)
                channel_append = json.load(append)

                for message in channel_append["messages"]:
                    if message["id"] not in existing_messages:
                        existing_messages.add(message["id"])
                        channel_json["messages"].append(message)

            os.remove(folder_path + filename)

    with open(folder_path + "channel.json", "w", encoding='utf-8') as update:
        print("Writing channel.json")
        json.dump(channel_json, update)


if __name__ == '__main__':
    update_all_messages()
