import os
import re
import shutil
import requests
import difflib
from typing import Dict, List, Tuple, Optional
import operator
import errno

import deck
import card

import mylogger

logger = mylogger.MAINLOGGER


def all_editions_magiccards_info(html: str) -> List[Tuple[Optional[str], str, str]]:
    part_regex = re.compile(
        r"<br><u><b>Editions:</b></u><br>(.*?)<br><u><b>Languages:</b></u><br>",
        flags=re.I | re.M | re.DOTALL)
    sub = part_regex.search(html).group(1).strip()
    current = re.search(r"\s?<b>\s?(.*?)\s?\((.*?)\)\s?</b>\s?<br>", sub, re.I)
    others = re.findall(r"\s?<a\shref=\s?\"([^\"]+?)\"\s?>\s?(.*?)\s?</a>\s?\((.*?)\)\s?<br>",
                        sub, re.I)  # type: List[Tuple[Optional[str], str, str]]
    others.append((None, str(current.group(1)), str(current.group(2))))
    return others


def get_image_link_parts(htmllink: str) -> Tuple[str, str, str]:
    htmllink = os.path.splitext(htmllink)[0]
    edition, language, number = htmllink.strip('/.').split(sep='/')
    return language, edition, number


def find_image(card: card.Card, source: str = "http://magiccards.info") -> List[str]:
    name = card.name.replace('//', '/')
    if card.version:
        name += " e:\"{0}\"".format(card.version)
    payload = {'q': name}
    res = requests.get(source + "/query", payload)
    res.raise_for_status()
    logger.debug("Search string: {0}".format(res.url))
    searchstr = r'img\s+src="({0}/scans/[^"\s]+)"\s+alt="([^"]*)"'.format(re.escape(source))
    others = all_editions_magiccards_info(res.text)
    l = []
    for m in others:
        if m[0] is not None:
            try:
                l.append(source + "/scans/" + '/'.join(get_image_link_parts(m[0])) + ".jpg")
            except StopIteration:
                pass
    matchiter = re.finditer(searchstr, res.text)
    t = ((difflib.SequenceMatcher(None, mo.group(2).lower(), card.name.lower()).ratio(), mo)
         for mo in matchiter)
    matchobj = max(t, key=operator.itemgetter(0))[1]
    outlist = [matchobj.group(1)]
    outlist.extend(l)
    return outlist


def get_all_images(names: deck.Deck, output_directory: str) -> Dict[card.Card, str]:
    logger.info("Loading images...", verbose_msg=os.path.abspath(output_directory))
    outnames = {}
    view = sorted(names.full_deck.items(), key=lambda x: (x[0].name, x[0].version), reverse=True)
    for card, num in view:
        if num > 0:
            if card not in outnames:
                try:
                    logger.info(verbose_msg="Loading {0}".format(card))
                    outname = get_image(card, output_directory)
                    outnames[card] = outname
                except (requests.exceptions.HTTPError, ValueError):
                    logger.warning("{0} not found".format(card))
    logger.info("Image loading, done!")
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
        links = find_image(card)
        response = None
        outputfile = None
        for link in links:
            search = re.search(r"/(\w+)/\w+\.(\w+)$", link)
            version, ext = search.group(1), search.group(2)
            outname += "[{0}].{1}".format(version, ext)
            outputfile = output_directory + '/' + outname
            response = requests.get(link, stream=True)
            if response.status_code == 200:
                break
        else:
            if response is None:
                raise RuntimeError("Bad card downloading. "
                                   "Either magiccards.info is offline or "
                                   "there are gremlins in the code")
            response.raise_for_status()
        with open(outputfile, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return outname
