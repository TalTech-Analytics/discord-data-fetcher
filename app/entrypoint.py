from channel.channel import update_all_messages
from channels.channels import update_channels
from guilds.guilds import update_guilds


def fetch_output():
    update_guilds()
    update_channels()
    update_all_messages()


if __name__ == '__main__':
    fetch_output()
