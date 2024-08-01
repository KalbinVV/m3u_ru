import json

import requests
from bs4 import BeautifulSoup

from fuzzywuzzy import fuzz


site_url = 'https://epg.iptvx.one/'


def parse_channel_ids_from_site(save_to_json: bool = False,
                                json_file_path: str = 'epg.json') -> dict[str, str]:
    page = requests.get(site_url)

    soup = BeautifulSoup(page.text, "html.parser")
    tbody = soup.find('tbody')

    channels_dict = dict()

    for tr in tbody.findAll('tr'):
        if len(tr.text) > 0:
            channel_tags = tr.findAll('td')

            channel_id = channel_tags[1].text

            for channel_name_tag in channel_tags[2].findAll('a'):
                channels_dict[channel_name_tag.text] = channel_id

    if save_to_json:
        with open(json_file_path, 'w') as f:
            json.dump(channels_dict, f)

    return channels_dict


def parse_channels_epg_dict_from_file(file_path: str = 'epg.json') -> dict[str, str]:
    with open(file_path, 'r') as f:
        return json.load(f)


def find_correct_epg_id(channel_name: str,
                        epg_dict: dict[str, str]) -> str:
    similar_channel_name = sorted(epg_dict.keys(), key=lambda name: fuzz.token_set_ratio(name, channel_name))[-1]

    return epg_dict[similar_channel_name]


def replace_channels_ids_to_correct(channels,
                                    epg_dict: dict[str, str]) -> None:
    for channel in channels:
        correct_tvg_id = find_correct_epg_id(channel.channel_name, epg_dict)

        channel.params['tvg-id'] = correct_tvg_id

        print(f'{channel.channel_name} set to tvg_id: {correct_tvg_id}')
