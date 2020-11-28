import subprocess
import json
import shutil
import os

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
        entrypoint: [ "dotnet", "/app/DiscordChatExporter.Cli.dll", "export", "--channel", "<CHANNEL_ID>", "-f", "Json" ]
        volumes:
            - /host/output/<GUILD_ID>/<CHANNEL_ID>/:/app/out
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
            except Exception:
                folder_path = "/host/output/" + guild_id + "/" + str(channel["id"]) + "/"
                shutil.rmtree(folder_path)


def update_channel(guild_id, channel_id):
    docker_compose_file = original_docker_compose.replace("<GUILD_ID>", guild_id).replace("<CHANNEL_ID>", channel_id)
    folder_path = "/host/output/" + guild_id + "/" + channel_id + "/"
    with open(folder_path + "docker-compose-discord-channel.yml", "w", encoding='utf8') as docker_compose:
        docker_compose.write(docker_compose_file)

    subprocess.call("docker-compose -f " + folder_path + "docker-compose-discord-channel.yml up", shell=True)
    subprocess.call("docker-compose -f " + folder_path + "docker-compose-discord-channel.yml down", shell=True)

    for filename in os.listdir(folder_path):
        if channel_id in filename:
            os.rename(folder_path + filename, folder_path + "channel.json")


if __name__ == '__main__':
    update_all_messages()
