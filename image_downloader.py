import os
import re
import shutil
import requests
from typing import Dict

import deck
import card


def find_image(card: card.Card, source: str = "http://magiccards.info") -> str:
    name = card.name.replace('//', '/')
    if card.version:
        name += " e:\"{0}\"".format(card.version)
    print('.', end='')
    payload = {'q': name}
    res = requests.get(source + "/query", payload)
    res.raise_for_status()
    print('.', end='')
    matchobj = re.search(r'img\s+src="({0}/scans/[^"\s]+)"'.format(re.escape(source)), res.text)
    print('.', end='')
    return matchobj.group(1)


def get_all_images(names: deck.Deck, output_directory: str) -> Dict[card.Card, str]:
    print("Loading images...")
    outnames = {}
    # outcounter = Counter()
    view = sorted(names.full_deck.items(), key=lambda x: (x[0].name, x[0].version), reverse=True)
    for card, num in view:
        if num > 0:
            if card in outnames:
                # outcounter[card] += num
                pass
            else:
                try:

                    print("\rdownloading {0}".format(card), end='')
                    outname = get_image(card, output_directory)
                    outnames[card] = outname
                    # outcounter.update(num * (card,))
                except (requests.exceptions.HTTPError, StopIteration):
                    print(card, "not found")
    print("\ndone!")
    return outnames


def name_to_fname(name: str) -> str:
    return name.replace('/', '%2F').lower()


def get_image(card: card.Card, output_directory: str) -> str:
    outname = name_to_fname(card.name)
    try:
        prog = re.compile(outname + (r"\[{0}\]".format(card.version) if card.version else r"(\[[^]]+?\])?"),
                          flags=re.IGNORECASE)
        existing_fname = next(f for f in os.listdir(output_directory)
                              if os.path.isfile(os.path.join(output_directory, f)) and
                              prog.fullmatch(os.path.splitext(f)[0]))
        return existing_fname
    except StopIteration:
        link = find_image(card)
        search = re.search(r"/(\w+)/\w+\.(\w+)$", link)
        version, ext = search.group(1), search.group(2)
        outname += "[{0}].{1}".format(version, ext)
        outputfile = output_directory + '/' + outname
        response = requests.get(link, stream=True)
        response.raise_for_status()
        with open(outputfile, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return outname

