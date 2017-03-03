import os
import re
import shutil
import requests
import difflib
from typing import Dict
import operator
import errno

import deck
import card
import logging

import mylogger
logger = mylogger.MAINLOGGER


def find_image(card: card.Card, source: str = "http://magiccards.info") -> str:
    name = card.name.replace('//', '/')
    if card.version:
        name += " e:\"{0}\"".format(card.version)
    print('.', end='')
    payload = {'q': name}
    res = requests.get(source + "/query", payload)
    res.raise_for_status()
    print('.', end='')
    searchstr = r'img\s+src="({0}/scans/[^"\s]+)"\s+alt="([^"]*)"'.format(re.escape(source))
    matchiter = re.finditer(searchstr, res.text)
    t = ((difflib.SequenceMatcher(None, mo.group(2).lower(), card.name.lower()).ratio(), mo)
         for mo in matchiter)
    matchobj = max(t, key=operator.itemgetter(0))[1]
    print('.', end='')
    return matchobj.group(1)


def get_all_images(names: deck.Deck, output_directory: str) -> Dict[card.Card, str]:
    print("Loading images...")
    print(os.path.abspath(output_directory))
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
                except (requests.exceptions.HTTPError, ValueError):
                    logger.warning("\n{0} not found".format(card))
    print("\ndone!")
    return outnames


def name_to_fname(name: str) -> str:
    return name.replace('/', '%2F').lower()


def get_image(card: card.Card, output_directory: str) -> str:
    try:
        os.makedirs(output_directory)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    outname = name_to_fname(card.name)
    try:
        prog = re.compile(
            outname + (r"\[{0}\]".format(card.version) if card.version else r"(\[[^]]+?\])?"),
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
