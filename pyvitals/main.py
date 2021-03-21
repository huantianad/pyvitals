import os
import re
import shutil

import requests
import yaml
import yaml.reader as reader


def get_site_data(verified_only=False):
    """
    Gets the site api and returns parsed json.
    If verified_only is True, this will only return verified levels.

    :param verified_only: Whether to only return verified levels only
    :return: Parsed json from site api.
    """

    url = 'https://script.google.com/macros/s/AKfycbzm3I9ENulE7uOmze53cyDuj7Igi7fmGiQ6w045fCRxs_sK3D4/exec'
    r = requests.get(url).json()

    if verified_only:
        return [x for x in r if x.get('verified')]
    else:
        return r


def get_url_filename(url: str):
    """
    Tries to get the file name from the download url of a level.
    If the url ends with .rdzip, the function assumes the url ends with the filename.
    Else, it uses Content-Disposition to try to get the filename.

    :param str url: The url of the level
    :return: The filename of the level
    """

    if url.endswith('.rdzip'):
        # When the filename already ends with the file extension, we can just snatch it from the url
        name = url.split('/')[-1]
    else:
        # Otherwise, we need to use some weird stuff to get it from the Content-Disposition header
        r = requests.get(url).headers.get('Content-Disposition')
        name = re.findall('filename=(.+)', r)[0].split(";")[0].replace('"', "")

    return name


def rename(path: str):
    if os.path.exists(path):
        # We need to loop through each possible filename, starting at 'filename (1)', then 'filename (2)', etc.
        # Once we get to a filename that doesn't exist, we exit the while loop and return this filename.
        # If the filename does exist, increment index, try the next number.'
        index = 2
        path = path.replace(".rdzip", "")  # Gets rid of the .rdzip extension, we add it back later on.

        while os.path.exists(f"{path} ({index}).rdzip"):
            index += 1

        return f"{path} ({index}).rdzip"
    else:
        # When the file doesn't exist, we don't need to do anything, so we can just directly return the filename
        return path


def download_level(url: str, path: str, do_rename=True, unzip=False):
    """
    Downloads a level from the specified url, uses get_url_filename() to find the filename, and put it in the path.
    If the keyword argument rename is True, this will try to automatically rename the file,
    if one with the same name already exists.
    If the keyword argument unzip is True, this will automatically unzip the file into a directory with the same name.

    :param url: The url of the level to download.
    :param path: The path to put the downloaded level in.
    :param do_rename: Whether to automatically rename the file.
    :param unzip: Whether to automatically unzip the file.
    :return: The full path to the downloaded level.
    """

    # Get the proper filename of the level, append it to the path to get the full path to the downloaded level.
    filename = get_url_filename(url)
    full_path = f"{path}/{filename}"

    # When enabled, use the rename function to find a unique filename
    if do_rename:
        full_path = rename(full_path)

    # Downloads the level, writes it to a file
    with open(f'{full_path}', 'wb') as file:
        r = requests.get(url)
        file.write(r.content)

    if unzip:
        unzip_level(full_path)

    return full_path  # Returns the final path to the downloaded level


def unzip_level(path: str):
    """
    Unzips the given level, and removes the old rdzip afterwards.

    :param path: Path to the level to unzip
    """

    # Remove the extension from the path as a temporary folder to extract the files to
    extension_less_path = path.replace('.rdzip', '')
    os.mkdir(extension_less_path)

    # Extracts the file into the temporary folder
    shutil.unpack_archive(path, extension_less_path, format="zip")

    # Removes the old rdzip, then renames the folder to have the .rdzip extension
    os.remove(path)
    os.rename(extension_less_path, path)


def parse_level(path: str, ignore_events=True):
    """
    Reads the rdlevel data and parses it to be used in python.
    Uses pyyaml because of trailing commas.
    Event data is not parsed by default, set ignore_events to False to enable it.

    :param path: Path to the .rdlevel to parse
    :param ignore_events:
    :return: The parsed level data
    """

    with open(path, "r", encoding="utf-8-sig") as file:
        fixed_file = file.read().replace("\t", "  ")  # YAML only accepts spaces, not tabs

        # parsing al of the level events is unnecessary for getting the metadata, so it's optional.
        if ignore_events:
            # When events are disabled, just nuke the whole section
            fixed_file = fixed_file.split('"events":')[0] + "}"
        else:
            # Fixes weird missing commas
            # Thanks WillFlame for the magic regex
            fixed_file = re.sub(r'\": ([0-9]|[1-9][0-9]|100|\"([a-zA-Z]|[0-9])*\") \"', '\": \1, \"', fixed_file)

        try:
            data = yaml.safe_load(fixed_file)
        except reader.ReaderError:
            # There's a chance that the level file has weird unicode, in which case it will error and come here.
            # This loop comprehension just nukes those weird characters, thanks J for the unicode in your one level
            fixed_file = "".join([x for x in fixed_file if not reader.Reader.NON_PRINTABLE.match(x)])
            data = yaml.safe_load(fixed_file)

        return data
