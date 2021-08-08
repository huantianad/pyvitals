from __future__ import annotations

import re
import shutil
from copy import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from zipfile import ZipFile, is_zipfile

import httpx
import rapidjson

from .exceptions import BadRDZipFile, BadURLFilename

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath, StrPath


def get_sheet_data(client: httpx.Client, verified_only=False) -> list[dict]:
    """
    Uses the level spreadsheet api to get all the levels.
    If verified_only is True, this will only return verified levels.

    Args:
        client (httpx.Client): The httpx client to use for the request.
        verified_only (bool, optional): Whether to only return verified levels only. Defaults to False.

    Returns:
        list[dict]: Parsed json from sheet api.
    """

    url = 'https://script.google.com/macros/s/AKfycbzm3I9ENulE7uOmze53cyDuj7Igi7fmGiQ6w045fCRxs_sK3D4/exec'
    json_data = client.get(url).json()
    json_data = [x for x in json_data if x.get('verified')] if verified_only else json_data

    return json_data


def get_setlists_url(client: httpx.Client, keep_none=False, trim_none=False) -> dict[str, list[str]]:
    """
    Gets all the urls for the levels on the setlists with a fancy google script.

    Args:
        client (httpx.Client): The httpx client to use for the request.
        keep_none (bool, optional): Whether to have Nones at all. Defaults to False.
        trim_none (bool, optional): Whether to trim Nones at the start and stop. Defaults to False.

    Returns:
        dict[str, list[str]]: [description]
    """

    url = 'https://script.google.com/macros/s/AKfycbzKbt6JDlvFs0jgR2AqGrjqb6UxnoXjVFmoU4QnEHbCc28Tx7rGMUG-lEm5NklqgBtX/exec'  # noqa:E501
    params = {'keepNull': str(keep_none).lower()}
    json_data = client.get(url, params=params).json()

    # This request will read a bunch of extra cells, possibly above and below the actual data, resulting
    # in a bunch of extra Nones. We can remove this if wanted
    if trim_none:
        json_data = {name: trim_list(urls) for name, urls in json_data.items()}

    return json_data


def trim_list(input_: list) -> list:
    """
    Removes any falsey values at the start and end of a list.

    Args:
        input_ (list): List to trim.

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


def get_filename(r: httpx.Response) -> str:
    """
    Extracts the filename from a httpx response.
    If the url ends with '.rdzip', we can assume that the last segment of the url is the filename,
    otherwise, we extract the filename from the Content-Disposition header.
    TODO: add better support for allowing user to choose which one to use.

    Args:
        r (httpx.Response): The response to get the filename response.

    Raises:
        BadURLFilename: Raised when unable to get a filename from the Content-Disposition header.

    Returns:
        str: The filename of the level.
    """

    url = str(r.url)

    if url.endswith('.rdzip'):
        name = url.rsplit('/', 1)[-1]
    else:
        header = r.headers.get('Content-Disposition')

        if header is None:
            raise BadURLFilename(f"Could not find Content-Disposition header for {url}", url)

        match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', header)

        if match is None:
            raise BadURLFilename(f"Could not extract filename from Content-Disposition for {url}", url)

        name = match.group(1)

    # Remove the characters that windows doesn't like in filenames
    for char in r'<>:"/\|?*':
        name = name.replace(char, '')

    return name


def get_filename_from_url(client: httpx.Client, url: str) -> str:
    """
    Wraps get_filename() with requests.get() to get the filename directly from a url.

    Args:
        client (httpx.Client): httpx client to use for the request
        url (str): The url to the level to get the filename of.

    Returns:
        str: The filename of the level.
    """

    with client.stream('GET', url) as r:
        r.raise_for_status()
        filename = get_filename(r)

    return filename


def rename(path: Path) -> Path:
    """
    Given some path, returns a file path that doesn't already exist.
    This is used to ensure that unique file names are always used.
    """

    if not path.exists():
        return path

    index = 2
    while path.with_stem(path.stem + f" ({index})").exists():
        index += 1

    return path.with_stem(path.stem + f" ({index})")


def download_level(client: httpx.Client, url: str, path: StrPath, unzip=False, fail_silently=False) -> Path:
    """
    Downloads a level from the specified url, uses get_url_filename() to find the filename, and put it in the path.

    If the keyword argument unzip is True, this will automatically unzip the file into a directory with the same name.
    Make sure to read the warning in unzip_level() if you're using unzip=True.

    Args:
        client (httpx.Client)  The httpx client to use for the request.
        url (str): The url of the level to download.
        path (StrPath): The path to put the downloaded level in.
        unzip (bool, optional): Whether to automatically unzip the file. Defaults to False.
        fail_silently (bool, optional): Whether to ignore errors silently. Defaults to False.

    Raises:
        httpx.HTTPStatusError: Raised when we receive an error (greater than 400) response code from the url.
        BadURLFilename: Raised when unable to get the level's filename.
        BadRDZipFile: Raised when the file isn't a valid zip file, or is unable to be unzipped.

    Returns:
        pathlib.Path: The full path to the downloaded level.
    """

    with client.stream('GET', url) as r:
        if fail_silently is False:
            r.raise_for_status()

        try:
            filename = get_filename(r)
        except BadURLFilename as e:
            if fail_silently is False:
                raise e
            filename = "BADFILENAME"

        full_path = Path(path, filename)
        full_path = rename(full_path)  # Ensure unique filename

        # Write level to file
        with open(full_path, 'wb') as file:
            for chunk in r.iter_bytes():
                file.write(chunk)

        if unzip:
            try:
                unzip_level(full_path)
            except BadRDZipFile as e:
                if fail_silently is False:
                    raise e

    return full_path


def unzip_level(path: Path) -> None:
    """
    Unzips the given level, and removes the old rdzip afterwards.

    Make sure you take care when unzipping levels from untrusted sources! Zip bombs exist.
    Please read the warnings in python's documentation for zipfile.ZipFile.extractall().

    Args:
        path (pathlib.Path): Path to the .rdzip to unzip
        remove_old (bool, optional): Whether to remove the old rdzip. Defaults to True.

    Raises:
        BadRDZipFile: Raised when the file isn't a valid zip file, or is unable to be unzipped.
    """

    if not is_zipfile(path):
        raise BadRDZipFile(f"{path} is not a valid zip file.", path)

    with TemporaryDirectory() as tempdir:
        try:
            with ZipFile(path, 'r') as zip:
                zip.extractall(tempdir)

        except OSError:
            raise BadRDZipFile(f"{path} was unable to be unzipped, perhaps it contains invalid file names.", path)

        else:
            path.unlink()
            shutil.move(tempdir, path)


def parse_level(path: StrOrBytesPath) -> dict:
    """
    Reads a .rdlevel file and parses it.
    Uses rapidjson as it allows for trailing commas, while still being somewhat performant.
    Attempts to fix problems with the rdlevel json by fixing some missing commas,
    as well as removing all newlines and tabs.

    Args:
        path (StrOrBytesPath): Path to the .rdlevel to parse

    Returns:
        dict: The parsed level data
    """

    with open(path, "r", encoding="utf-8-sig") as file:
        text = file.read()

        # Fixes weird missing commas. Thanks WillFlame for the magic regex
        text = re.sub(r'\": ([0-9]|[1-9][0-9]|100|\"([a-zA-Z]|[0-9])*\") \"', r'": \1, "', text)

        # Fixes bad newlines
        # TODO: Make this less destructive
        text = re.sub(r'(\r\n|\n|\r|\t)', '', text)

        # Use rapidjson as it allows for trailing commas
        data = rapidjson.loads(text, parse_mode=rapidjson.PM_TRAILING_COMMAS)

        return data


def parse_rdzip(path: 'StrPath') -> dict:
    """
    Parses the level data directly from an .rdzip file, assumes main.rdlevel as the level to parse.
    This will unzip it to a temporary directory and use parse_level to parse it.

    Args:
        path (StrPath): Path to the .rdzip to parse

    Returns:
        dict: The parsed level data
    """

    with TemporaryDirectory() as tempdir:
        with ZipFile(path, 'r') as zip:
            zip.extractall(tempdir)

        # The actual rdlevel will be in the folder, named main.rdlevel
        level_path = Path(tempdir, "main.rdlevel")
        output = parse_level(level_path)

    return output


def parse_url(client: httpx.Client, url: str) -> dict:
    """
    Parses the level data from an url, uses download_level to download and unzip with parse_level to parse.

    Args:
        client (httpx.Client): httpx client to use for the request
        url (str): Url for the level to download and parse

    Returns:
        dict: The parsed level data
    """

    with TemporaryDirectory() as tempdir:
        path = download_level(client, url, tempdir, unzip=True)

        # The actual rdlevel will be in the folder, named main.rdlevel
        level_path = path / "main.rdlevel"
        output = parse_level(level_path)

    return output
