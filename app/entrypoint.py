from channel.channel import update_all_messages
from channels.channels import update_channels
from guilds.guilds import update_guilds
import sys

sout = sys.stdout


def fetch_output():
    update_guilds()
    sys.stdout = sout
    update_channels()
    sys.stdout = sout
    update_all_messages()


if __name__ == '__main__':
    fetch_output()
