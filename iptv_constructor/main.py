import re
import time
from dataclasses import dataclass
from typing import Optional

from requests import get, Response


@dataclass
class ChannelInfo:
    channel_name: str
    ext_inv_id: int
    category_name: Optional[str]
    url: str
    params: dict[str, str]

    def __hash__(self):
        return hash(self.channel_name)


def check_url_status(url: str) -> bool:
    print(url)

    headers = {"Range": "bytes=0-10"}  # first 10 bytes

    request_start_time = time.perf_counter()

    try:
        result = get(url, headers, stream=True, timeout=3)

        request_time = time.perf_counter() - request_start_time

        print(f'Запрос выполнился за {round(request_time, 2)} секунд')
    except (Exception, ):
        return False

    return result.status_code == 200


def parse_params(params: Optional[str]) -> dict[str, str]:
    if params is None:
        return {}

    params_dict = {}
    param_regex = r'(?P<param_name>[\w-]+)=\"(?P<param_value>[^\t\n\r\f\v]+)\"'

    for value in re.split(r'(?<=\")\s+', params):
        for match in re.finditer(param_regex, value):
            params_dict[match.group('param_name')] = match.group('param_value')

    return params_dict


def parse_file(file_path: str) -> list[ChannelInfo]:
    regex = r"#EXTINF:(?P<ext_inv_id>\-?\d+)(?P<params>[^\t\n\r\f\v]+)?,(?P<channel_name>[^\t\n\r\f\v]+)\n(" \
            r"#EXTVLCOPT:(?P<extl>[^\t\n\r\f\v]+)\n)?(#EXTGRP:(?P<category_name>[^\t\n\r\f\v]+)\n)?(?P<url>[" \
            r"^\t\n\r\f\v][^\t\n\r\f\v]+)"

    channels: list[ChannelInfo] = list()

    with open(file_path, 'r') as f:
        content = f.read()

        for match in re.finditer(regex, content):
            channel_name = match.group('channel_name')
            ext_inv_id = int(match.group('ext_inv_id'))
            url = match.group('url')
            params = parse_params(match.group('params'))
            category_name = match.group('category_name')

            if not category_name:
                category_name = params.get('group-title', 'Без категории')

            channels.append(ChannelInfo(channel_name,
                                        ext_inv_id,
                                        category_name,
                                        url,
                                        params))

    return channels


def split_channels_by_categories(channels: list[ChannelInfo]) -> dict[str, set[ChannelInfo]]:
    channels_by_categories = dict()

    for channel in channels:
        channels_list = channels_by_categories.setdefault(channel.category_name, set())

        channels_list.add(channel)

    return channels_by_categories


def make_m3u_file(channels: list[ChannelInfo],
                  output_filename: str,
                  required_params: Optional[list[str]] = None,
                  not_check_categories: Optional[list[str]] = None,
                  rename_categories: Optional[dict[str, str]] = None,
                  dont_add_not_work_channels: bool = True) -> None:

    with open(output_filename, 'w') as f:
        f.write('#EXTM3U\n')

        channels_by_categories = split_channels_by_categories(channels)

        for category_name, channels_list in channels_by_categories.items():
            if len(channels_list) == 0:
                continue

            if rename_categories and category_name in rename_categories:
                category_name = rename_categories[category_name]

            f.write(f'\n#{category_name} (Начало)\n\n')

            for channel in channels_list:
                channel.category_name = category_name

                if not_check_categories and category_name not in not_check_categories:
                    if not check_url_status(channel.url):
                        if dont_add_not_work_channels:
                            continue

                        channel.category_name = 'Перестали работать'

                f.write(f'#EXTINF:{channel.ext_inv_id}')

                if not required_params:
                    for param_name, param_value in channel.params.items():
                        f.write(f' {param_name}="{param_value}"')
                else:
                    for param_name in required_params:
                        param_value = channel.params.get(param_name, None)

                        if param_value:
                            f.write(f' {param_name}="{param_value}"')

                    f.write(f' group-title="{channel.category_name}"')

                f.write(f',{channel.channel_name}\n')
                f.write(channel.url)
                f.write('\n\n')

            f.write(f'#{category_name} (Конец)\n')


def main():
    channels = parse_file('stream.m3u')

    make_m3u_file(channels, 'stream-formatted.m3u',
                  required_params=['tvg-id', 'tvg-logo'],
                  not_check_categories=['Немецкие'],
                  rename_categories={'Germany VIP': 'Немецкие'})


if __name__ == '__main__':
    main()
