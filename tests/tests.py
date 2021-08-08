import hashlib
import os
import unittest
from glob import glob
from multiprocessing.pool import ThreadPool
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import pyvitals


class Tests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.testing_levels = [
            {
                "url": "https://cdn.discordapp.com/attachments/611380148431749151/624806831050457099/Bill_Wurtz_-_Chips.rdzip",  # noqa:E501
                "name": "Bill_Wurtz_-_Chips.rdzip",
                "size": 314311,
                "md5sum": "83d6224500de3e43535c4eca87afb2df"
            },
            {
                "url": "https://cdn.discordapp.com/attachments/611380148431749151/624806831050457099/Bill_Wurtz_-_Chips.rdzip",  # noqa:E501
                "name": "Bill_Wurtz_-_Chips (2).rdzip",
                "size": 314311,
                "md5sum": "83d6224500de3e43535c4eca87afb2df"
            },
            {
                "url": "https://www.dropbox.com/s/ppomi3tg6ovgkuo?dl=1",
                "name": "9999_1 - 23.exe - YY.rdzip",
                "size": 95249907,
                "md5sum": "89ba382901a96287a7e9653a13b2661c"
            },
            {
                "url": "https://drive.google.com/uc?export=download&id=1LZ5KWG4KCL1Or-kSYimbVaSFIoTrGgsI",
                "name": "Lemon Demon - Angry People.rdzip",
                "size": 22337449,
                "md5sum": "188e43b30feb9bcb0848e422843ff894"
            },
            {
                "url": "https://cdn.discordapp.com/attachments/611380148431749151/738933182044438639/The_Lick_in_all_12_keys.rdzip",  # noqa:E501
                "name": "The_Lick_in_all_12_keys.rdzip",
                "size": 725621,
                "md5sum": "314423b4408319d366b3d0c24606ea87"
            },
        ]

    def test_filenames(self):
        """Tests discord, google drive, and dropbox urls"""

        urls = [
            "https://cdn.discordapp.com/attachments/611380148431749151/624806831050457099/Bill_Wurtz_-_Chips.rdzip",
            "https://www.dropbox.com/s/ppomi3tg6ovgkuo?dl=1",
            "https://drive.google.com/uc?export=download&id=1LZ5KWG4KCL1Or-kSYimbVaSFIoTrGgsI",
            "http://www.bubbletabby.com/MATTHEWGU4_-_Hail_Satan_Metal_Cover.rdzip",
        ]
        correct_names = [
            "Bill_Wurtz_-_Chips.rdzip",
            "9999_1 - 23.exe - YY.rdzip",
            "Lemon Demon - Angry People.rdzip",
            "MATTHEWGU4_-_Hail_Satan_Metal_Cover.rdzip",
        ]

        with httpx.Client() as client:
            names = [pyvitals.get_filename_from_url(client, url) for url in urls]

        self.assertEqual(names, correct_names)

    def test_download_unzip(self):
        with httpx.Client() as client:
            with TemporaryDirectory() as tempdir:
                for x in self.testing_levels:
                    print(pyvitals.download_level(client, x['url'], tempdir, unzip=True))

    def test_all_filenames(self):
        """Attempt to get the filenames of all levels on the spreadsheet."""
        with httpx.Client() as client:
            urls = [x['download_url'] for x in pyvitals.get_sheet_data(client)]
            results = ThreadPool(40).imap_unordered(lambda x: pyvitals.get_filename_from_url(client, x), urls)

            for result in results:
                pass

    def test_sheet(self):
        """Basic sanity checks for site data."""
        with httpx.Client() as client:
            all = pyvitals.get_sheet_data(client, verified_only=False)
            verified = pyvitals.get_sheet_data(client, verified_only=True)

        self.assertGreater(len(all), len(verified))
        self.assertGreater(len(all), 2000)
        self.assertGreater(len(verified), 1000)

    def test_setlist(self):
        """Basic sanity check for setlist data."""
        with httpx.Client() as client:
            setlists = pyvitals.get_setlists_url(client, keep_none=False, trim_none=False)
        setlists_len = [len(x) for x in setlists.values()]

        self.assertEqual(setlists_len[:9], [38] * 9)

    def test_download_levels(self):
        """Check the filename, filesize, and hash of a few preset levels"""

        with TemporaryDirectory() as tempdir:
            with httpx.Client() as client:
                for level in self.testing_levels:
                    level_path = pyvitals.download_level(client, level['url'], tempdir)

                    self.assertEqual(level['name'], os.path.basename(level_path))
                    self.assertEqual(level['size'], os.path.getsize(level_path))
                    with open(level_path, 'rb') as file:
                        self.assertEqual(level['md5sum'], hashlib.md5(file.read()).hexdigest())

    def test_parse_all_levels(self):
        """Attempts to parse all my downloaded levels to see if there are any errors."""

        levels_folder_path = '/home/huantian/Documents/Levels/'  # Change this when running on your machine
        levels = glob(os.path.join(levels_folder_path, '*', '*.rdlevel'))

        for level_path in levels:
            try:
                pyvitals.parse_level(level_path)
            except Exception as e:
                print(level_path)
                raise e

    def test_parse_urls(self):
        """Attempts to parse a few levels from urls"""

        with httpx.Client() as client:
            for level in self.testing_levels:
                pyvitals.parse_url(client, level['url'])

    def test_rename(self):
        """Tests the rename function."""

        with TemporaryDirectory() as tempdir:
            file = Path(tempdir, "test.asdf")

            renamed = pyvitals.rename(file)
            self.assertEqual(renamed, file)

            renamed.touch()
            renamed = pyvitals.rename(file)
            self.assertEqual(renamed, file.with_stem("test (2)"))

            renamed.touch()
            renamed = pyvitals.rename(file)
            self.assertEqual(renamed, file.with_stem("test (3)"))

            file.with_stem("test (4)").touch()
            renamed = pyvitals.rename(file)
            self.assertEqual(renamed, file.with_stem("test (3)"))

            renamed.mkdir()
            renamed = pyvitals.rename(file)
            self.assertEqual(renamed, file.with_stem("test (5)"))


if __name__ == '__main__':
    unittest.main()
