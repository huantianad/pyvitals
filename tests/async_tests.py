import asyncio
import hashlib
import os
import unittest
from tempfile import TemporaryDirectory

import pyvitals
import httpx


async def gather_with_concurrency(n: int, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks))


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_download_levels(self):
        """Check the filename, filesize, and hash of a few preset levels"""

        levels = [
            {
                "url": "https://cdn.discordapp.com/attachments/611380148431749151/624806831050457099/Bill_Wurtz_-_Chips.rdzip",  # noqa:E501
                "name": "Bill_Wurtz_-_Chips.rdzip",
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
        levels2 = [
            {
                "url": "https://cdn.discordapp.com/attachments/611380148431749151/624806831050457099/Bill_Wurtz_-_Chips.rdzip",  # noqa:E501
                "name": "Bill_Wurtz_-_Chips (2).rdzip",
                "size": 314311,
                "md5sum": "83d6224500de3e43535c4eca87afb2df"
            },
        ]

        async def check_level(level: dict) -> None:
            level_path = await pyvitals.async_download_level(client, level['url'], tempdir)

            self.assertEqual(level['name'], os.path.basename(level_path))
            self.assertEqual(level['size'], os.path.getsize(level_path))
            with open(level_path, 'rb') as file:
                self.assertEqual(level['md5sum'], hashlib.md5(file.read()).hexdigest())

        with TemporaryDirectory() as tempdir:
            async with httpx.AsyncClient() as client:
                await asyncio.gather(*[check_level(level) for level in levels])
                await asyncio.gather(*[check_level(level) for level in levels2])

    async def test_filenames(self):
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

        async with httpx.AsyncClient() as client:
            names = await asyncio.gather(*[pyvitals.async_get_filename_from_url(client, url) for url in urls])

        self.assertEqual(names, correct_names)

    async def test_all_filenames(self):
        """Attempt to get the filenames of all levels on the spreadsheet."""

        async with httpx.AsyncClient(timeout=20) as client:
            async def test(url: str) -> str:
                return await pyvitals.async_get_filename_from_url(client, url)

            urls = [x['download_url'] for x in await pyvitals.async_get_sheet_data(client)]
            await gather_with_concurrency(77, *[test(url) for url in urls])

    async def test_sheet(self):
        """Basic sanity checks for site data."""

        async with httpx.AsyncClient() as client:
            all = await pyvitals.async_get_sheet_data(client, verified_only=False)
            verified = await pyvitals.async_get_sheet_data(client, verified_only=True)

        self.assertGreater(len(all), len(verified))
        self.assertGreater(len(all), 2000)
        self.assertGreater(len(verified), 1000)

    async def test_setlist(self):
        """Basic sanity check for setlist data."""

        async with httpx.AsyncClient() as client:
            setlists = await pyvitals.async_get_setlists_url(client, keep_none=False, trim_none=False)
        setlists_len = [len(x) for x in setlists.values()]

        self.assertEqual(setlists_len[:9], [38] * 9)


if __name__ == '__main__':
    unittest.main()
