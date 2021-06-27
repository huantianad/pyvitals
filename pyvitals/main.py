import json
import os
import re
import shutil
from copy import copy
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import requests


def get_site_data(verified_only=False) -> list[dict]:
    """
    Uses the level spreadsheet api to get all the levels.
    If verified_only is True, this will only return verified levels.

    Args:
        verified_only (bool, optional): Whether to only return verified levels only. Defaults to False.

    Returns:
        list[dict]: Parsed json from site api.
    """

    url = 'https://script.google.com/macros/s/AKfycbzm3I9ENulE7uOmze53cyDuj7Igi7fmGiQ6w045fCRxs_sK3D4/exec'
    r = requests.get(url).json()

    if verified_only:
        return [x for x in r if x.get('verified')]
    else:
        return r


def get_setlists_url(keep_none=False, trim_none=False) -> dict[str, list[str]]:
    """
    Gets all the urls for the levels on the setlists with a fancy google script.

    Args:
        keep_none (bool, optional): Whether to have Nones at all. Defaults to False.
        trim_none (bool, optional): Whether to trim Nones at the start and stop. Defaults to False.

    Returns:
        dict[str, list[str]]: [description]
    """

    url = 'https://script.google.com/macros/s/AKfycbzKbt6JDlvFs0jgR2AqGrjqb6UxnoXjVFmoU4QnEHbCc28Tx7rGMUG-lEm5NklqgBtX/exec'  # noqa:E501
    params = {'keepNull': str(keep_none).lower()}
    r = requests.get(url, params=params).json()

    # This request will read a bunch of extra cells, possibly above and below the actual data, resulting
    # in a bunch of extra Nones. We can remove this if wanted
    if trim_none:
        r = {name: trim_list(urls) for name, urls in r.items()}

    return r


def trim_list(input_: list) -> list:
    """
    Removes any falsey values at the start and end of a list.

    Args:
        input_list (list): List to trim.

    Returns:
        list: A trimmed version of the input.
    """

    input_list = copy(input_)

    while input_list and not input_list[0]:
        del input_list[0]

    while input_list and not input_list[-1]:
        del input_list[-1]

    return input_list


# def get_orchard_data():
#     sql = """
#     SELECT  q.*,
#             t.tag,
#             t.seq AS tag_seq,
#             a.author,
#             a.seq AS author_seq
#     FROM    (
#                 SELECT   l.*,
#                             Row_number() OVER ( ORDER BY uploaded DESC, last_updated DESC ) AS rn
#                 FROM     levels AS l
#             ) AS q
#     LEFT JOIN level_tag AS t ON t.id = q.id
#     LEFT JOIN level_author AS a ON a.id = q.id
#     ORDER BY rn
#     """

#     params = {
#         "_size": "max_",
#         "_shape": "array",
#         "sql": " ".join(sql.split()),
#     }
#     levels = paginate('https://api.rhythm.cafe/orchard.json', params=params)

#     print(len(levels))

#     return list(levels)


# def paginate(url: str, params: dict):
#     items = []
#     while url:
#         response = requests.get(url, params=params)
#         print(response.url)
#         try:
#             url = response.links.get("next").get("url")
#         except AttributeError:
#             url = None
#         items.extend(response.json())
#     return items


def get_filename(r: requests.Request) -> str:
    """
    Extracts the filename from the Content-Disposition header of a request.

    Args:
        r (requests.Request): A requests object from getting the url of a level

    Returns:
        str: The filename of the level
    """

    h = r.headers.get('Content-Disposition')
    print(h)
    name = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', h).groups()[0]

    # Remove the characters that windows doesn't like in filenames
    for char in r'<>:"/\|?*':
        name = name.replace(char, '')

    return name


def get_url_filename(url: str) -> str:
    """
    A wrapper for get_filename, gets the filename directly from a url.
    Uses requests.get(url, stream=True)

    Args:
        url (str): The url to get the path of

    Returns:
        str: The filename of the level
    """

    r = requests.get(url, stream=True)
    name = get_filename(r)

    return name


def rename(path: str) -> str:
    """
    Given some path, returns a file path that doesn't already exist.
    This is used to ensure that unique file names are always used.
    """

    if os.path.exists(path):
        index = 2
        path = path.replace(".rdzip", "")  # Gets rid of the .rdzip extension, we add it back later on.

        while os.path.exists(f"{path} ({index}).rdzip"):
            index += 1

        return f"{path} ({index}).rdzip"
    else:
        # When the file doesn't exist, we don't need to do anything, so we can just directly return the filename
        return path


def download_level(url: str, path: str, unzip=False) -> str:
    """
    Downloads a level from the specified url, uses get_url_filename() to find the filename, and put it in the path.
    If the keyword argument unzip is True, this will automatically unzip the file into a directory with the same name.

    Args:
        url (str): The url of the level to download.
        path (str): The path to put the downloaded level in.
        unzip (bool, optional): Whether to automatically unzip the file. Defaults to False.

    Returns:
        str: The full path to the downloaded level.
    """

    r = requests.get(url, stream=True)

    # Get the proper filename of the level, append it to the path to get the full path to the downloaded level.
    filename = get_filename(r)
    full_path = os.path.join(path, filename)

    # Ensure unique filename
    full_path = rename(full_path)

    # Downloads the level, writes it to a file
    with open(full_path, 'wb') as file:
        file.write(r.content)

    if unzip:
        unzip_level(full_path)

    return full_path


def unzip_level(path: str) -> None:
    """
    Unzips the given level, and removes the old rdzip afterwards.

    Args:
        path (str): Path to the .rdzip to unzip
    """

    with TemporaryDirectory() as tempdir:
        with ZipFile(path, 'r') as zip:
            zip.extractall(tempdir)
        os.remove(path)
        shutil.move(tempdir, path)


def parse_level(path: str, parse_events=False) -> dict:
    """
    Reads the rdlevel data and parses it.
    Uses pyyaml because of trailing commas.
    Event data is not parsed by default, set parse_events to True to enable it.

    Args:
        path (str): Path to the .rdlevel to parse
        parse_events (bool, optional): Whether or not to parse events. Defaults to False.

    Returns:
        dict: The parsed level data
    """

    with open(path, "r", encoding="utf-8-sig") as file:
        text = file.read()

        # parsing al of the level events is unnecessary for getting the metadata, so it's optional.
        if not parse_events:
            # When events are disabled, remove everything past "events"
            text = text.split('"events":')[0] + '}'
        else:
            # Fixes weird missing commas. Thanks WillFlame for the magic regex
            text = re.sub(r'\": ([0-9]|[1-9][0-9]|100|\"([a-zA-Z]|[0-9])*\") \"', r'": \1, "', text)
            # Fix trailing commas
            text = re.sub(r'}, ?\n\t]', r'}\n\t]', text)
            text = text.replace(', }', ' }')
            # Fix weird newlines
            text = re.sub(r'(\r\n|\n|\r|\t)', '', text)

        data = json.loads(text)

        return data


def parse_rdzip(path: str, parse_events=False) -> dict:
    """
    Parses the level data directly from an .rdzip file, assumes main.rdlevel as the level to parse.
    This will unzip it to a temporary directory and use parse_level to parse it.
    Event data is not parsed by default, set parse_events to True to enable it.

    Args:
        path (str): Path to the .rdzip to parse
        parse_events (bool, optional): Whether or not to parse events. Defaults to False.

    Returns:
        dict: The parsed level data
    """

    with TemporaryDirectory() as tempdirpath:
        with ZipFile(path, 'r') as zip:
            zip.extractall(tempdirpath)

        # The actual rdlevel will be in the folder, named main.rdlevel
        level_path = os.path.join(tempdirpath, "main.rdlevel")
        output = parse_level(level_path, parse_events=parse_events)

    return output


def parse_url(url: str, parse_events=False) -> dict:
    """
    Parses the level data from an url, uses download_level to download and unzip with parse_level to parse.
    Event data is not parsed by default, set parse_events to True to enable it.

    Args:
        url (str): Url for the level to download and parse
        parse_events (bool, optional): Whether or not to parse events. Defaults to False.

    Returns:
        dict: The parsed level data
    """

    with TemporaryDirectory() as tempdirpath:  # temporary folder to download the level to
        path = download_level(url, tempdirpath, unzip=True)

        # The actual rdlevel will be in the folder, named main.rdlevel
        level_path = os.path.join(path, "main.rdlevel")
        output = parse_level(level_path, parse_events=parse_events)

    return output
