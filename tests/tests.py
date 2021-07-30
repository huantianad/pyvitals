import asyncio
import hashlib
import os
import unittest
from glob import glob
from multiprocessing.pool import ThreadPool
from tempfile import TemporaryDirectory

import pyvitals
import aiohttp


async def gather_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks))


class Tests(unittest.TestCase):
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

        names = [pyvitals.get_filename_from_url(url) for url in urls]

        self.assertEqual(names, correct_names)

    def test_all_filenames(self):
        urls = [x['download_url'] for x in pyvitals.get_sheet_data()]
        results = ThreadPool(40).imap_unordered(pyvitals.get_filename_from_url, urls)

        for result in results:
            pass

    def test_sheet(self):
        """Basic sanity checks for length of lists of levels."""
        all = pyvitals.get_sheet_data(verified_only=False)
        verified = pyvitals.get_sheet_data(verified_only=True)

        self.assertGreater(len(all), len(verified))
        self.assertGreater(len(all), 2000)
        self.assertGreater(len(verified), 1000)

    def test_setlist(self):
        setlists = pyvitals.get_setlists_url(keep_none=False, trim_none=False)
        setlists_len = [len(x) for x in setlists.values()]

        self.assertEqual(setlists_len[:9], [38] * 9)

        print([len(x) for x in setlists.values()])

    def test_download_level(self):
        levels = [
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

        with TemporaryDirectory() as tempdir:
            for level in levels:
                level_path = pyvitals.download_level(level['url'], tempdir)

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


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_download_levels(self):
        levels = [
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

        async def check_level(level: dict) -> None:
            level_path = await pyvitals.async_download_level(session, level['url'], tempdir)

            self.assertEqual(level['name'], os.path.basename(level_path))
            self.assertEqual(level['size'], os.path.getsize(level_path))
            with open(level_path, 'rb') as file:
                self.assertEqual(level['md5sum'], hashlib.md5(file.read()).hexdigest())

        with TemporaryDirectory() as tempdir:
            async with aiohttp.ClientSession() as session:
                await asyncio.gather(*[check_level(level) for level in levels])

    async def test_all_filenames(self):
        async def test_url(url: str) -> None:
            await pyvitals.async_get_filename_from_url(session, url)

        urls = [x['download_url'] for x in pyvitals.get_sheet_data()]
        async with asyncio.Semaphore(3):
            async with aiohttp.ClientSession() as session:
                await gather_with_concurrency(77, *[test_url(urls) for urls in urls])


if __name__ == '__main__':
    unittest.main()
