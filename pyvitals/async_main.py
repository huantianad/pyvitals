from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import httpx

from .main import get_filename, parse_level, rename, trim_list, unzip_level

if TYPE_CHECKING:
    from _typeshed import StrPath


async def async_get_sheet_data(client: httpx.AsyncClient, verified_only=False) -> list[dict]:
    """
    Uses the level spreadsheet api to get all the levels.
    If verified_only is True, this will only return verified levels.

    Args:
        client (httpx.AsyncClient): The async httpx client to use for the request.
        verified_only (bool, optional): Whether to only return verified levels only. Defaults to False.

    Returns:
        list[dict]: Parsed json from sheet api.
    """

    url = 'https://script.google.com/macros/s/AKfycbzm3I9ENulE7uOmze53cyDuj7Igi7fmGiQ6w045fCRxs_sK3D4/exec'
    resp = await client.get(url)
    json_data = resp.json()

    json_data = [x for x in json_data if x.get('verified')] if verified_only else json_data

    return json_data


async def async_get_setlists_url(client: httpx.AsyncClient, keep_none=False, trim_none=False) -> dict[str, list[str]]:
    """
    Gets all the urls for the levels on the setlists with a fancy google script.

    Args:
        client (httpx.AsyncClient: The async httpx client to use for the request.
        keep_none (bool, optional): Whether to have Nones at all. Defaults to False.
        trim_none (bool, optional): Whether to trim Nones at the start and stop. Defaults to False.

    Returns:
        dict[str, list[str]]: [description]
    """

    url = 'https://script.google.com/macros/s/AKfycbzKbt6JDlvFs0jgR2AqGrjqb6UxnoXjVFmoU4QnEHbCc28Tx7rGMUG-lEm5NklqgBtX/exec'  # noqa:E501
    params = {'keepNull': str(keep_none).lower()}
    resp = await client.get(url, params=params)
    json_data = resp.json()

    # This request will read a bunch of extra cells, possibly above and below the actual data, resulting
    # in a bunch of extra Nones. We can remove this if wanted
    if trim_none:
        json_data = {name: trim_list(urls) for name, urls in json_data.items()}

    return json_data


async def async_download_level(client: httpx.AsyncClient, url: str, path: StrPath, unzip=False) -> Path:
    """
    Downloads a level from the specified url, uses get_url_filename() to find the filename, and put it in the path.
    If the keyword argument unzip is True, this will automatically unzip the file into a directory with the same name.

    Args:
        client (httpx.AsyncClient): The async httpx client to use for the request.
        url (str): The url of the level to download.
        path (str): The path to put the downloaded level in.
        unzip (bool, optional): Whether to automatically unzip the file. Defaults to False.

    Raises:
        httpx.HTTPStatusError: Raised when we receive an error (greater than 400) response code from the url.
        BadURLFilename: Raised when unable to get the level's filename.
        BadRDZipFile: Raised when the file isn't a valid zip file, or is unable to be unzipped.

    Returns:
        pathlib.Path: The full path to the downloaded level.
    """

    async with client.stream('GET', url) as resp:  # type: ignore
        resp: httpx.Response
        resp.raise_for_status()

        filename = get_filename(resp)
        full_path = Path(path, filename)
        full_path = rename(full_path)  # Ensure unique filename

        # Write level to file
        with open(full_path, 'wb') as file:
            async for chunk in resp.aiter_bytes():
                file.write(chunk)

    if unzip:
        unzip_level(full_path)

    return full_path


async def async_get_filename_from_url(client: httpx.AsyncClient, url: str) -> str:
    """
    Wraps get_filename() with httpx.AsyncClient.get() to get the filename directly from a url.

    Args:
        client (httpx.AsyncClient): The async httpx client to use for the request.
        url (str): The url to the level to get the filename of.

    Returns:
        str: The filename of the level
    """

    async with client.stream('GET', url) as resp:  # type: ignore
        resp: httpx.Response
        resp.raise_for_status()
        filename = get_filename(resp)

    return filename


async def async_parse_url(client: httpx.AsyncClient, url: str) -> dict:
    """
    Parses the level data from an url, uses download_level to download and unzip with parse_level to parse.

    Args:
        client (httpx.AsyncClient): The async httpx client to use for the request.
        url (str): The url to the level to download and parse.

    Returns:
        dict: The parsed level data
    """

    with TemporaryDirectory() as tempdirpath:
        path = await async_download_level(client, url, tempdirpath, unzip=True)

        # The actual rdlevel will be in the folder, named main.rdlevel
        level_path = Path(path, "main.rdlevel")
        output = parse_level(level_path)

    return output
