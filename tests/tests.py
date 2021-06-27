import unittest
from pprint import pprint

import pyvitals


class Tests(unittest.TestCase):
    def test_filenames(self):
        """Tests discord, google drive, and dropbox urls"""
        urls = [
            "https://cdn.discordapp.com/attachments/611380148431749151/624806831050457099/Bill_Wurtz_-_Chips.rdzip",
            "https://www.dropbox.com/s/ppomi3tg6ovgkuo?dl=1",
            "https://drive.google.com/uc?export=download&id=1LZ5KWG4KCL1Or-kSYimbVaSFIoTrGgsI"
        ]
        correct_names = [
            "Bill_Wurtz_-_Chips.rdzip",
            "9999_1 - 23.exe - YY.rdzip",
            "Lemon Demon - Angry People.rdzip"
        ]

        names = [pyvitals.get_url_filename(url) for url in urls]

        self.assertEqual(names, correct_names)

    def test_sheet(self):
        """Basic sanity checks for length of lists of levels."""
        all = pyvitals.get_site_data(verified_only=False)
        verified = pyvitals.get_site_data(verified_only=True)

        self.assertGreater(len(all), len(verified))
        self.assertGreater(len(all), 2000)
        self.assertGreater(len(verified), 1000)

    def test_setlist(self):
        setlists = pyvitals.get_setlists_url(keep_none=False, trim_none=False)
        setlists_len = [len(x) for x in setlists.values()]

        self.assertEqual(setlists_len[:9], [38] * 9)

        pprint(setlists)
        print([len(x) for x in setlists.values()])


if __name__ == '__main__':
    unittest.main()
