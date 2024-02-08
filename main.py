from httpx import Client
from base64 import b64encode
from colorama import Fore, init
from time import strftime
import re
import json

init(autoreset=True)

def p(text: str) -> None:
    print(
        f"{Fore.LIGHTWHITE_EX}[{Fore.CYAN}{strftime('%H:%M:%S')}{Fore.LIGHTWHITE_EX}] {text}"
        .replace('[+]', f'[{Fore.LIGHTGREEN_EX}+{Fore.LIGHTWHITE_EX}]')
        .replace('[*]', f'[{Fore.LIGHTYELLOW_EX}*{Fore.LIGHTWHITE_EX}]')
        .replace('[>]', f'[{Fore.CYAN}>{Fore.LIGHTWHITE_EX}]')
        .replace('[-]', f'[{Fore.RED}-{Fore.LIGHTWHITE_EX}]')
    )

class Scrape:
    def __init__(self, token: str, id: str) -> None:
        self.token = token
        self.id = id
        self.baseurl = f"https://discord.com/api/v9/guilds/{self.id}"
        self.session = Client()
        self.headers = {"Authorization": self.token}

    def do_request(self, url) -> dict:
        return self.session.get(url=url, headers=self.headers).json()

    def get_channel(self, channel_id) -> dict:
        return self.do_request(f"{self.baseurl}/channels/{channel_id}")

    def get_channels(self) -> dict:
        return self.do_request(f"{self.baseurl}/channels")

    def get_info(self) -> dict:
        return self.do_request(self.baseurl)

    def get_data(self, scope) -> dict:
        if scope.lower() == 'server':
            info = self.get_info()
            channels = self.get_channels()
            return {
                "info": info,
                "channels": channels,
                "roles": info.get("roles", []),
                "emojis": info.get("emojis", []),
            }
        else:
            channel = self.get_channel(scope)
            return {
                "channel": channel
            }

def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'[^\w\-_]', '', text)
    return text

def query_save_format() -> str:
    while True:
        user_input = input("Enter the format to save the file as (e.g., 'guild-servername-channelname'): ").strip()
        if re.match(r'^[\w\-]+$', user_input):
            return user_input
        else:
            print("Invalid format. Please use only letters, numbers, hyphens, and underscores.")

def get_scope() -> str:
    while True:
        scope_input = input("Enter 'server' to collect data from the entire server or a channel ID for specific channel data: ").strip()
        if scope_input.lower() == 'server' or re.match(r'^\d+$', scope_input):
            return scope_input
        else:
            print("Invalid input. Please enter 'server' or a valid channel ID.")

if __name__ == "__main__":
    config = json.loads(open("config.json", "r").read())
    token = config["token"]

    scope = get_scope()

    source_scraper = Scrape(token, input("⭐ Source Server ID: "))
    source_data = source_scraper.get_data(scope)

    preprocessed_data = {}
    if scope.lower() == 'server':
        preprocessed_data = {
            "info": {
                key: preprocess_text(value) if isinstance(value, str) else value for key, value in source_data["info"].items()
            },
            "channels": [
                {
                    key: preprocess_text(value) if isinstance(value, str) else value for key, value in channel.items()
                } for channel in source_data["channels"]
            ]
        }
    else:
        preprocessed_data = {
            "channel": {
                key: preprocess_text(value) if isinstance(value, str) else value for key, value in source_data["channel"].items()
            }
        }

    save_format = query_save_format()
    print(f"Save format selected: {save_format}")

    # Implement logic to save the preprocessed data based on the chosen format
