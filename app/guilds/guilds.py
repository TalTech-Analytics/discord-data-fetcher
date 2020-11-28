import subprocess
import os
import re
import json

log_pattern = r"^.*\s(\d*) \| (.*)$"


def update_guilds():
    collect_data()
    process_data()
    cleanup()


def cleanup():
    os.remove("/analyzer/tmp/guilds.log")
    subprocess.call("docker-compose -f guilds/docker-compose-discord-guilds.yml down --remove-orphans", shell=True)


def process_data():
    try:
        update_guilds_json()
    except Exception as e:
        clean_up(e)
        try_again()


def try_again():
    print("Trying again")
    try:
        update_guilds_json()
    except Exception as e:
        print("Failed second time:", e)
        print("Skipping")


def clean_up(e):
    print("Failed updating guilds:", e)
    os.remove("/analyzer/discord-output/guilds.json")


def collect_data():
    with open("/analyzer/tmp/guilds.log", "a", encoding='utf-8') as output:
        subprocess.call("docker-compose -f guilds/docker-compose-discord-guilds.yml up", shell=True, stdout=output)


def update_guilds_json():
    with open("/analyzer/tmp/guilds.log", "r", encoding='utf-8') as output:
        content = "\n".join(output.readlines())

        matches = re.finditer(log_pattern, content, re.MULTILINE)
        guilds_list = []
        guilds_list_duplicates = set()
        guilds_json = {"guilds": guilds_list}

        guilds_json, guilds_list = fetch_existing(guilds_json, guilds_list, guilds_list_duplicates)
        update_existing(guilds_list, guilds_list_duplicates, matches)
        dump_existing(guilds_json)


def dump_existing(guilds_json):
    with open("/analyzer/discord-output/guilds.json", "w", encoding='utf-8') as guilds_output:
        json.dump(guilds_json, guilds_output)


def update_existing(guilds_list, guilds_list_duplicates, matches):
    for matchNum, match in enumerate(matches, start=1):
        print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
                                                                            end=match.end(), match=match.group()))
        if match.group(2) not in guilds_list_duplicates:
            folder_path = "/analyzer/discord-output/" + match.group(1)
            try:
                os.mkdir(folder_path)
                print("Making a folder as it didn't exist:", folder_path)
            except Exception as e:
                print("Failed making a folder:", e)
                pass
            guilds_list.append({"name": match.group(2), "id": int(match.group(1))})


def fetch_existing(guilds_json, guilds_list, guilds_list_duplicates):
    if os.path.isfile("/analyzer/discord-output/guilds.json"):
        with open("/analyzer/discord-output/guilds.json", "r", encoding='utf-8') as guilds_existing:
            guilds_json = json.load(guilds_existing)
            guilds_list = guilds_json["guilds"]
            for guild in guilds_list:
                guilds_list_duplicates.add(guild["name"])
    return guilds_json, guilds_list


if __name__ == '__main__':
    update_guilds()
