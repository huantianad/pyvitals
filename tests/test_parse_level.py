import unittest
import os
from glob import glob

from pyvitals import parse_level


class TestParseLevels(unittest.TestCase):
    def test_(self):
        # self.assertEqual(True, False)
        username = 'david'

        dir_list = glob(rf"C:\Users\{username}\Documents\Rhythm Doctor\Levels\*")
        remove_paths = [rf"C:\Users\{username}\Documents\Rhythm Doctor\Levels\sync.json",
                        rf"C:\Users\{username}\Documents\Rhythm Doctor\Levels\yeeted"]

        for remove_path in remove_paths:
            if os.path.exists(remove_path):
                dir_list.remove(remove_path)

        for dir_ in dir_list:
            print(dir_)
            parse_level(dir_ + "/main.rdlevel", ignore_events=True)


if __name__ == '__main__':
    unittest.main()
