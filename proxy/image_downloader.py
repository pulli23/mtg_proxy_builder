import os
import re
import shutil
import requests
import difflib
from typing import Dict, List, Tuple, Optional, Sequence, Generator, Iterable, Union
import operator
import errno

from bs4 import BeautifulSoup, Tag, NavigableString

import deck
import card

import mylogger

logger = mylogger.MAINLOGGER


def load_magic_card(card: card.Card, source: str = "http://magiccards.info") -> requests.Response:
    if card.edition and card.collectors_number and card.language:
        url = "{0}/{1}.html".format(source, '/'.join((card.edition,
                                                      card.language,
                                                      str(card.collectors_number))))
        payload = {}
    else:
        name = card.name.replace('//', '/')
        if card.edition:
            name += " e:\"{0}\"".format(card.edition)
        payload = {'q': name}
        url = source + "/query"
    res = requests.get(url, payload)
    logger.debug("Lookup url: {0}".format(res.url))
    res.raise_for_status()
    return res


def make_soup(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html5lib")
    return soup


def find_htmltext_tables(soup: Tag) -> List[Tag]:
    v = soup.find_all('table')
    v = [tab for tab in v if len(tab.find_all('a')) > 0
         and len(tab.find_all('img')) > 0
         and (not tab.has_attr("id") or tab["id"] != "nav")]
    return v


def unpack_cardtable(cardtable: Tag) -> Tuple[Tag, Tag, Tag]:
    search = cardtable
    tb = search.find("tbody", recursive=False)
    if tb is not None:
        search = tb
    tr = search.find("tr", recursive=False)
    if tr is not None:
        search = tr
    img, info, ex_info, *residu = search.find_all("td", recursive=False)
    return img, info, ex_info


def safe_unpack_cardtables(cardtables: Iterable[Tag]) \
        -> Generator[Tuple[Tag, Tag, Tag], None, None]:
    for table in cardtables:
        try:
            yield unpack_cardtable(table)
        except StopIteration:
            pass


def pick_best_matching_card(card: card.Card, card_info_seq: Iterable[Tuple[Tag, Tag, Tag]]) \
        -> Tuple[Tag, Tag, Tag]:
    def get_relative_match(match: str):
        return difflib.SequenceMatcher(None, match.lower(), card.name.lower()).ratio()

    return max(card_info_seq,
               key=lambda x: get_relative_match(next(x[1].find("a").stripped_strings)))


def analyse_hyperref(href: str) -> Tuple[str, str, str]:
    htmllink = os.path.splitext(href)[0]
    edition, language, number = htmllink.strip('/.').split(sep='/')
    return language, edition, number


def get_other_edition_links(ex_info_tag: Tag) -> Generator[str, None, None]:
    tag = ex_info_tag
    while not tag.string:
        tt = tag.find_all(True, recursive=False)
        tag = tt[0]
    parent_tag = tag.parent
    tags = parent_tag.find_all("u")

    start, n = next((tag, n) for n, tag in enumerate(tags)
                    if "editions" in tag.get_text().lower())
    if n < len(tags):
        end = tags[n + 1]
    else:
        end = None
    curtag = start
    while True:
        curtag = curtag.next_sibling
        if curtag != end:
            if curtag.name == "a":
                yield curtag["href"]
        else:
            break


def get_main_edition_link(info_tag: Tag) -> str:
    return info_tag.find("a")["href"]


def get_imagelink_from_tag(img_tag: Tag) -> str:
    return img_tag.find("img")["src"]


def find_card_tablecells(card: card.Card, source: str = "http://magiccards.info") \
        -> Tuple[Tag, Tag, Tag]:
    res = load_magic_card(card, source)
    soup = make_soup(res.text)
    cardtables = find_htmltext_tables(soup)
    card_info_list = safe_unpack_cardtables(cardtables)
    # noinspection PyTypeChecker
    return pick_best_matching_card(card, card_info_list)


def find_card_urls(card: card.Card, source: str = "http://magiccards.info") -> List[str]:
    _, info_tag, ex_info_tag = find_card_tablecells(card, source)
    yield get_main_edition_link(info_tag)
    yield from get_other_edition_links(ex_info_tag)


def find_image_url(urliter: Union[Iterable[str], Generator[str, None, None]],
                   source: str = "http://magiccards.info") \
        -> Generator[str, None, None]:
    # noinspection PyTypeChecker
    for url in urliter:
        language, edition, number = analyse_hyperref(url)
        yield "{0}/scans/{1}.jpg".format(source, '/'.join((language, edition, number)))


def get_all_images(names: deck.Deck, output_directory: str) -> Dict[card.Card, str]:
    logger.info("Loading images...", verbose_msg=os.path.abspath(output_directory))
    outnames = {}
    view = sorted(names.full_deck.items(), key=lambda x: (x[0].name, x[0].edition), reverse=True)
    for card, num in view:
        if num > 0 and card not in outnames:
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
        return download_card_image(card, output_directory)


def download_card_image(card: card.Card, output_directory: str) -> str:
    outname = name_to_fname(card.name)
    gen_card_urls = find_card_urls(card)
    links = find_image_url(gen_card_urls)
    response = None
    outputfile = None
    # noinspection PyTypeChecker
    for link in links:
        search = re.search(r"/(\w+)/(\w+)\.(\w+)$", link)
        version, num, ext = search.group(1), search.group(2), search.group(3)
        outname += "[{0},{2}].{1}".format(version, ext, num)
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
