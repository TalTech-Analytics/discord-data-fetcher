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
        env_file:
            - /host/app/.env
        environment:
            GUILDID: <GUILD_ID>
        entrypoint: [ "dotnet", "/app/DiscordChatExporter.Cli.dll", "export", "--channel", "<CHANNEL_ID>", "--after", "<AFTER>", "-f", "Json" ]
        volumes:
            - /host/output/<GUILD_ID>/<CHANNEL_ID>/:/app/out/
"""


def update_all_messages():
    with open("/host/output/guilds.json", "r", encoding='utf8') as guilds:
        guilds_json = json.load(guilds)
        for guild in guilds_json["guilds"]:
            update_guild_messages(str(guild['id']))


def update_guild_messages(guild_id):
    with open("/host/output/" + guild_id + "/channels.json", "r", encoding='utf8') as channels:
        channels_json = json.load(channels)
        for channel in channels_json["channels"]:
            try:
                update_channel(guild_id, str(channel["id"]))
            except Exception as e:
                print("Failed updating guild messages:", e)
                folder_path = "/host/output/" + guild_id + "/" + str(channel["id"]) + "/"
                print("Deleting channel:", folder_path)
                shutil.rmtree(folder_path)


def update_channel(guild_id, channel_id):
    folder_path = "/host/output/" + guild_id + "/" + channel_id + "/"
    after = get_latest_timestamp(folder_path)
    print("Fetching all messages after:", after)
    docker_compose_file = original_docker_compose \
        .replace("<GUILD_ID>", guild_id) \
        .replace("<CHANNEL_ID>", channel_id) \
        .replace("<AFTER>", after)

    with open(folder_path + "docker-compose-discord-channel.yml", "w", encoding='utf8') as docker_compose:
        docker_compose.write(docker_compose_file)

    subprocess.call("docker-compose -f " + folder_path + "docker-compose-discord-channel.yml up", shell=True)
    subprocess.call("docker-compose -f " + folder_path + "docker-compose-discord-channel.yml down", shell=True)

    if os.path.isfile(folder_path + "channel.json"):
        print("Updating existing", folder_path)
        update_existing_messages(channel_id, folder_path)
    else:
        print("Creating new", folder_path)
        create_new_messages(channel_id, folder_path)


def get_latest_timestamp(folder_path):
    after = None
    if os.path.isfile(folder_path + "channel.json"):
        with open(folder_path + "channel.json", "r", encoding='utf8') as channel_existing:
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
        if channel_id in filename:
            os.rename(folder_path + filename, folder_path + "channel.json")


def update_existing_messages(channel_id, folder_path):
    existing_messages = set()

    with open(folder_path + "channel.json", "r", encoding='utf8') as channel_existing:
        print("Reading channel.json")
        channel_json = json.load(channel_existing)
        for message in channel_json["messages"]:
            existing_messages.add(message["id"])

    for filename in os.listdir(folder_path):
        if channel_id in filename:
            print("Found new file", filename)

            with open(folder_path + filename, "r", encoding='utf8') as append:
                print("Appending ", filename)
                channel_append = json.load(append)

                for message in channel_append["messages"]:
                    if message["id"] not in existing_messages:
                        existing_messages.add(message["id"])
                        channel_json["messages"].append(message)

            os.remove(folder_path + filename)

    with open(folder_path + "channel.json", "w", encoding='utf8') as update:
        print("Writing channel.json")
        json.dump(channel_json, update)


if __name__ == '__main__':
    update_all_messages()
