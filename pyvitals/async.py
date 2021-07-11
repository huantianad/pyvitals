import os
import re
from tempfile import TemporaryDirectory

import aiohttp

from .main import rename, trim_list, unzip_level, parse_level


async def aget_sheet_data(session: aiohttp.ClientSession, verified_only=False) -> list[dict]:
    """
    Uses the level spreadsheet api to get all the levels.
    If verified_only is True, this will only return verified levels.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        verified_only (bool, optional): Whether to only return verified levels only. Defaults to False.

    Returns:
        list[dict]: Parsed json from sheet api.
    """

    url = 'https://script.google.com/macros/s/AKfycbzm3I9ENulE7uOmze53cyDuj7Igi7fmGiQ6w045fCRxs_sK3D4/exec'
    async with session.get(url) as resp:
        json_data = await resp.json()

    json_data = [x for x in json_data if x.get('verified')] if verified_only else json_data

    return json_data


async def aget_setlists_url(session: aiohttp.ClientSession, keep_none=False, trim_none=False) -> dict[str, list[str]]:
    """
    Gets all the urls for the levels on the setlists with a fancy google script.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        keep_none (bool, optional): Whether to have Nones at all. Defaults to False.
        trim_none (bool, optional): Whether to trim Nones at the start and stop. Defaults to False.

    Returns:
        dict[str, list[str]]: [description]
    """

    url = 'https://script.google.com/macros/s/AKfycbzKbt6JDlvFs0jgR2AqGrjqb6UxnoXjVFmoU4QnEHbCc28Tx7rGMUG-lEm5NklqgBtX/exec'  # noqa:E501
    params = {'keepNull': str(keep_none).lower()}
    async with session.get(url, params=params) as resp:
        json_data = await resp.json()

    # This request will read a bunch of extra cells, possibly above and below the actual data, resulting
    # in a bunch of extra Nones. We can remove this if wanted
    if trim_none:
        json_data = {name: trim_list(urls) for name, urls in json_data.items()}

    return json_data


async def adownload_level(session: aiohttp.ClientSession, url: str, path: str, unzip=False) -> str:
    """
    Downloads a level from the specified url, uses get_url_filename() to find the filename, and put it in the path.
    If the keyword argument unzip is True, this will automatically unzip the file into a directory with the same name.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (str): The url of the level to download.
        path (str): The path to put the downloaded level in.
        unzip (bool, optional): Whether to automatically unzip the file. Defaults to False.

    Returns:
        str: The full path to the downloaded level.
    """

    # Get the proper filename of the level, append it to the path to get the full path to the downloaded level.
    filename = await aget_filename(session, url)
    full_path = os.path.join(path, filename)

    # Ensure unique filename
    full_path = rename(full_path)

    # Write level to file
    with open(full_path, 'wb') as file:
        async with session.get(url) as resp:
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break
                file.write(chunk)

    if unzip:
        unzip_level(full_path)

    return full_path


async def aget_filename(session: aiohttp.ClientSession, url: str) -> str:
    """
    Extracts the filename from the Content-Disposition header of a request.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        r (requests.Request): A requests object from getting the url of a level

    Returns:
        str: The filename of the level
    """

    if url.endswith('.rdzip'):
        name = url.rsplit('/', 1)[-1]
    else:
        async with session.get(url) as resp:
            h = resp.headers.get('Content-Disposition')
        name = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', h).groups()[0]

    # Remove the characters that windows doesn't like in filenames
    for char in r'<>:"/\|?*':
        name = name.replace(char, '')

    return name


async def aparse_url(session: aiohttp.ClientSession, url: str) -> dict:
    """
    Parses the level data from an url, uses download_level to download and unzip with parse_level to parse.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (str): Url for the level to download and parse

    Returns:
        dict: The parsed level data
    """

    with TemporaryDirectory() as tempdirpath:  # temporary folder to download the level to
        path = await adownload_level(session, url, tempdirpath, unzip=True)

        # The actual rdlevel will be in the folder, named main.rdlevel
        level_path = os.path.join(path, "main.rdlevel")
        output = parse_level(level_path)

    return output
