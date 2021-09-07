from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Optional

import httpx

from .main import get_filename, parse_rdzip, rename, trim_list, unzip_level

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


async def async_download_level(client: httpx.AsyncClient, url: str, path: StrPath,
                               filename: Optional[str] = None) -> Path:
    """
    Downloads a level from the given url into the given path.
    Automatically deterimes the filename from the url or request headers, unless manually given a filename.
    If you manually give this a filename, this *will* overwrite any existing files.
    When automatically determining the filename, a unique name is ensured.

    Args:
        client (httpx.AsyncClient): The async httpx client to use for the request.
        url (str): The url of the level to download.
        path (StrPath): The path to put the downloaded level in.
        filename (str, optional): What to name the level, if None given, will automatically determine it from url.

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

        if filename is None:
            url_filename = get_filename(resp)
            full_path = Path(path, url_filename)
            full_path = rename(full_path)  # Ensure unique filename
        else:
            full_path = Path(path, filename)

        try:
            # Write level to file
            with full_path.open('wb') as file:
                async for chunk in resp.aiter_bytes():
                    file.write(chunk)

        except Exception as e:
            # Clean up after ourselves here if something goes wrong when writing to file.
            full_path.unlink()
            raise e

    return full_path


async def async_download_unzip(client: httpx.AsyncClient, url: str, output_path: StrPath,
                               create_subfolder=False) -> Path:
    """
    Downloads a level into a temporary folder with download_level(), then unzips it into the given path.

    Make sure you take care when unzipping levels from untrusted sources! Zip bombs exist.
    Please read the warnings in python's documentation for zipfile.ZipFile.extractall().

    Args:
        client (httpx.AsyncClient): The async httpx client to use for the request.
        url (str): The url of the level to download.
        path (StrPath): The path to put the unzipped level contents in.
        create_subfolder (bool, optional): Whether to unzip the level into a subfolder based on filename.

    Raises:
        httpx.HTTPStatusError: Raised when we receive an error (greater than 400) response code from the url.
        BadURLFilename: Raised when unable to get the level's filename.
        BadRDZipFile: Raised when the file isn't a valid zip file, or is unable to be unzipped.

    Returns:
        pathlib.Path: The full path to the unzipped level.
    """

    with TemporaryDirectory() as tempdir:
        zipped_path = await async_download_level(client, url, tempdir)
        output_path = (rename(Path(output_path, zipped_path.stem)) if create_subfolder
                       else Path(output_path))

        unzip_level(zipped_path, output_path)

    return output_path


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
    Parses the level data from an url, uses download_level to download with parse_rdzip to parse.

    Args:
        client (httpx.AsyncClient): The async httpx client to use for the request.
        url (str): The url to the level to download and parse.

    Returns:
        dict: The parsed level data
    """

    with TemporaryDirectory() as tempdirpath:
        path = await async_download_level(client, url, tempdirpath)
        output = parse_rdzip(path)

    return output
