import os
import re
import shutil
import requests
from typing import Dict, Generator, Iterable, Union

from bs4 import Tag

import deck
import card
import mylogger
import card_downloader as card_dl

logger = mylogger.MAINLOGGER


def get_imagelink_from_tag(img_tag: Tag) -> str:
    return img_tag.find("img")["src"]


def find_image_url(urliter: Union[Iterable[str], Generator[str, None, None]],
                   source: str = "http://magiccards.info") \
        -> Generator[str, None, None]:
    # noinspection PyTypeChecker
    for url in urliter:
        edition, language, number = card_dl.analyse_hyperref(url)
        yield "{0}/scans/{1}.jpg".format(source,
                                         '/'.join((language,
                                                   card_dl.fix_magiccards_info_code(edition),
                                                   number))
                                         )


def get_all_images(names: deck.Deck, output_directory: str, session: requests.Session = None) \
        -> Dict[card.Card, str]:
    logger.info("Loading images...", verbose_msg=os.path.abspath(output_directory))
    outnames = {}
    view = sorted(names.full_deck.items(), key=lambda x: (x[0].name, x[0].edition), reverse=True)
    for card, num in view:
        if num > 0 and card not in outnames:
            try:
                logger.info(verbose_msg="Loading {0}".format(card))
                outname = get_image(card, output_directory, session)
                outnames[card] = outname
            except (requests.exceptions.HTTPError, ValueError):
                logger.warning("{0} not found".format(card))
    logger.info("Image loading, done!")
    return outnames


def name_to_fname(name: str) -> str:
    return name.replace('/', '%2F').lower()


def get_image(card: card.Card, output_directory: str, session: requests.Session = None) -> str:
    os.makedirs(output_directory, exist_ok=True)

    outname = name_to_fname(card.name)
    try:
        if card.edition:
            if card.collectors_number is not None:
                ex = r"\[{0},{1}\]".format(card.edition, card.collectors_number)
            else:
                ex = r"\[{0}(,\d+)?\]".format(card.edition)
        else:
            ex = r"(\[[^]]+?\])?"
        prog = re.compile(outname + ex, flags=re.IGNORECASE)
        existing_fname = next(f for f in os.listdir(output_directory)
                              if os.path.isfile(os.path.join(output_directory, f)) and
                              prog.fullmatch(os.path.splitext(f)[0]))
        logger.debug("Using existing file \"{0}\"".format(existing_fname))
        return existing_fname
    except StopIteration:
        return download_card_image(card, output_directory, session)


def download_card_image(card: card.Card, output_directory: str, session: card_dl.CardDownloader) \
        -> str:
    outname = name_to_fname(card.name)
    analyzer = session.make_html_analyzer(card.name, card.edition, card.collectors_number, card.language)
    gen_card_urls = analyzer.find_card_urls()
    links = find_image_url(gen_card_urls)
    response = None
    outputfile = None
    # noinspection PyTypeChecker
    for link in links:
        search = re.search(r"/(\w+)/(\w+)\.(\w+)$", link)
        version, num, ext = search.group(1), search.group(2), search.group(3)
        outname += "[{0},{2}].{1}".format(version, ext, num)
        outputfile = output_directory + '/' + outname
        response = session.session.get(link, stream=True)
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
