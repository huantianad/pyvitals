import unittest
from glob import glob
from collections import defaultdict
from json import dump
from re import split

import pyvitals


class Tests(unittest.TestCase):
    # def test_parse(self):
    #     dir_list = glob(r"/home/huantian/Documents/Levels/*/")
    #     dir_list.remove('/home/huantian/Documents/Levels/yeeted/')

    #     output = defaultdict(lambda: defaultdict(int))

    #     for dir_ in dir_list:
    #         data = pyvitals.parse_level(dir_ + "main.rdlevel", ignore_events=True)

    #         authors = split(',| and | & ', data['settings']['author'])
    #         authors = [x.strip() for x in authors]
    #         chars = [x['character'] for x in data['rows']]

    #         for author in authors:
    #             for char in chars:
    #                 output[author][char] += 1

    #     output = {key: dict(sorted(value.items(), key=lambda x: x[1], reverse=True)) for key, value in output.items()}

    #     # with open('output.json', 'w+') as file:
    #     #     dump(output, file, indent=4)

    def test_api(self):
        # site = pyvitals.get_site_data()
        orchard = pyvitals.get_orchard_data()
        # print(orchard)
        # orchard_not_workshop = [x for x in orchard if x['source_id'] != "workshop"]

        # site_urls = [x['download_url'] for x in site]
        # orchard_urls = [x['url'] for x in orchard_not_workshop]

        # print(len(orchard))

        # print(len(site))
        # print(len(orchard))
        # print(len(orchard_not_workshop))

        # print([x for x in site if x['song'] == "Chirp"])
        # print([x for x in orchard_not_workshop if x['song'] == "Chirp"])

        # print([x for x in orchard_urls if x not in site_urls])
        # print([x for x in site_urls if x not in orchard_urls])

    # def test_download(self):
    #     asdf = pyvitals.download_level("https://cdn.discordapp.com/attachments/611380148431749151/738933182044438639/The_Lick_in_all_12_keys.rdzip",
    #                                    './', unzip=True)


if __name__ == '__main__':
    unittest.main()
