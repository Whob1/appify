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
        self.token      = token
        self.id         = id
        self.baseurl    = f"https://discord.com/api/v9/guilds/{self.id}"
        self.session    = Client()
        self.headers    = {"Authorization": self.token}

    def do_request(self, url) -> dict:
        return self.session.get(
            url = url,
            headers = self.headers,
        ).json()

    def get_channels(self) -> dict:
        return self.do_request(f"{self.baseurl}/channels")

    def get_info(self) -> dict:
        return self.do_request(self.baseurl)

    def get_data(self) -> dict:
        info = self.get_info()
        channels = self.get_channels()

        return {
            "info"      : info,
            "channels"  : channels,
            "roles"     : info.get("roles", []),
            "emojis"    : info.get("emojis", []),
        }

def preprocess_text(text: str) -> str:
    # Lowercase the text
    text = text.lower()
    # Remove whitespace and replace with underscores
    text = re.sub(r'\s+', '_', text)
    # Remove invalid characters
    text = re.sub(r'[^\w\-_]', '', text)
    return text

def query_save_format() -> str:
    while True:
        user_input = input("Enter the format to save the file as (e.g., 'guild-servername-channelname'): ").strip()
        if re.match(r'^[\w\-]+$', user_input):
            return user_input
        else:
            print("Invalid format. Please use only letters, numbers, hyphens, and underscores.")

if __name__ == "__main__":
    config = json.loads(open("config.json", "r").read())
    token = config["token"]

    source_server_id = input("⭐ Source Server ID: ")

    # Get source server information
    source_scraper = Scrape(token, source_server_id)
    source_data = source_scraper.get_data()

    # Preprocess all text data
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

    # Query user for save format
    save_format = query_save_format()
    print(f"Save format selected: {save_format}")

    # Example of production usage:
    # This script would be used by a server admin or owner to extract information about their Discord server,
    # such as channel names and server information, and preprocess the text data to remove invalid characters.
    # Then, the user would be prompted to specify the format in which they want to save the file, ensuring it follows
    # a standardized naming convention for easier organization and retrieval of data in the future.
