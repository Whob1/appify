from httpx import Client
from base64 import b64encode
from colorama import Fore, init
from time import strftime
import re
import json
import csv
import os
import time

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
        self.baseurl = f'https://discord.com/api/v9/guilds/{self.id}'
        self.session = Client()
        self.headers = {'Authorization': 'Bearer ' + os.getenv('DISCORD_TOKEN')}

    def do_request(self, url) -> dict:
        response = self.session.get(url=url, headers=self.headers).json()
        if response.status_code == 429:  # We hit the rate limit
            retry_after = float(response.headers.get('Retry-After', 0))
            print(f'Rate limited. Waiting for {retry_after} seconds.')
            time.sleep(retry_after)
            return self.do_request(url)  # Retry the request
        else:
            return response.json()

    def fetch_messages(self, channel_id, limit=100, before=None):
        url = f'{self.baseurl}/channels/{channel_id}/messages?limit={limit}'
        if before:
            url += f'&before={before}'
        response = self.session.get(url=url, headers=self.headers)
        if response.status_code == 429:  # We hit the rate limit
            retry_after = float(response.headers.get('Retry-After', 0))
            print(f'Rate limited. Waiting for {retry_after} seconds.')
            time.sleep(retry_after)
            return self.fetch_messages(channel_id, limit, before)  # Retry the request
        elif response.status_code == 200:
            messages = response.json()
            if len(messages) < limit:
                return messages  # No more messages left to fetch
            else:
                last_message_id = messages[-1]['id']
                return messages + self.fetch_messages(channel_id, limit, last_message_id)
        else:
            print(f'Failed to fetch messages: {response.status_code}')
            return []

if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')

    scope = get_scope()

    source_scraper = Scrape(token, input('â­ Source Server ID: '))
    source_data = source_scraper.get_data(scope)

    preprocessed_data = {}
    if scope.lower() == 'server':
        preprocessed_data = {
            'info': {
                key: preprocess_text(value) if isinstance(value, str) else value for key, value in source_data['info'].items()
            },
            'channels': [
                {
                    key: preprocess_text(value) if isinstance(value, str) else value for key, value in channel.items()
                } for channel in source_data['channels']
            ]
        }
    else:
        preprocessed_data = {
            'channel': {
                key: preprocess_text(value) if isinstance(value, str) else value for key, value in source_data['channel'].items()
            }
        }

    save_format = query_save_format()
    file_name = save_format + '_' + (preprocessed_data.get('info', {}).get('name', 'data') if scope.lower() == 'server' else 'channel_' + scope)
    save_data(preprocessed_data, save_format, file_name)
