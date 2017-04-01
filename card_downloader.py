import os
import requests
import difflib
import re
from collections import Counter
import itertools
import functools
from typing import List, Tuple, Iterable, Generator, Union, Dict, Optional, Sequence

from bs4 import BeautifulSoup, Tag

import card
import mylogger
import mana_types

logger = mylogger.MAINLOGGER


def fix_magiccards_info_code(shortcode: str) -> str:
    codes = {
        "nem": "ne"
    }
    return codes.get(shortcode, shortcode)


def _get_literal_url(edition: str, language: str, collectors_number: int,
                     source: str = "http://magiccards.info") -> Tuple[str, Dict[str, str]]:
    url = "{0}/{1}.html".format(source, '/'.join((fix_magiccards_info_code(edition),
                                                  language, str(collectors_number))))
    payload = {}
    return url, payload


def _get_lookup_url(name: str, edition: str = None, language: str = None,
                    source: str = "http://magiccards.info") -> Tuple[str, Dict[str, str]]:
    name = name.replace('//', '/')
    if edition:
        name += " e:\"{0}\"".format(edition)
        if language:
            name += "/{0}".format(language)
    payload = {'q': name}
    url = source + "/query"
    return url, payload


@functools.lru_cache(maxsize=512)
def load_magic_card(name: str = None, edition: str = None, collectors_number: int = None,
                    language: str = None, source: str = "http://magiccards.info",
                    session: requests.Session = None) \
        -> requests.Response:
    if session is None:
        session = requests
    if name is None and (edition or collectors_number is not None or language):
        raise ValueError("Bad inputs")
    if edition and collectors_number is not None and language:
        url, payload = _get_literal_url(edition, language, collectors_number, source)
    else:
        url, payload = _get_lookup_url(name, edition, language, source)

    res = session.get(url, params=payload)
    logger.debug("Lookup url: {0}".format(res.url))
    res.raise_for_status()
    return res


def _make_soup(html: str) -> BeautifulSoup:
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


def pick_best_matching_card(name: str, card_info_seq: Iterable[Tuple[Tag, Tag, Tag]]) \
        -> Tuple[Tag, Tag, Tag]:
    def get_relative_match(match: str):
        return difflib.SequenceMatcher(None, match.lower(), name.lower()).ratio()
    try:
        return max(card_info_seq,
                   key=lambda x: get_relative_match(next(x[1].find("a").stripped_strings)))
    except ValueError:
        raise ValueError("card '{0}' not found".format(name))


def analyse_hyperref(href: str) -> Tuple[str, str, str]:
    htmllink = os.path.splitext(href)[0]
    edition, language, number = htmllink.strip('/.').split(sep='/')
    return edition, language, number


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


def get_main_name(info_tag: Tag) -> str:
    return info_tag.find("a").string


def find_card_tablecells(name: str = None, edition: str = None, collectors_number: int = None,
                         language: str = None, source: str = "http://magiccards.info",
                         session: requests.Session = None) \
        -> Tuple[Tag, Tag, Tag]:
    res = load_magic_card(name, edition, collectors_number, language, source, session)
    soup = _make_soup(res.text)
    cardtables = find_htmltext_tables(soup)
    card_info_list = safe_unpack_cardtables(cardtables)
    if name is not None:
        # noinspection PyTypeChecker
        return pick_best_matching_card(name, card_info_list)
    else:
        # noinspection PyTypeChecker
        return next(card_info_list)


def find_card_urls(name_or_card: "Union[card.Card, str]" = None,
                   edition: str = None, collectors_number: int = None, language: str = None,
                   source: str = "http://magiccards.info",
                   session: requests.Session = None) \
        -> Generator[str, None, None]:
    try:
        _, info_tag, ex_info_tag = find_card_tablecells(name_or_card.name,
                                                        name_or_card.edition,
                                                        name_or_card.collectors_number,
                                                        name_or_card.language,
                                                        source, session)
    except AttributeError:
        _, info_tag, ex_info_tag = find_card_tablecells(name_or_card, edition, collectors_number,
                                                        language, source, session)

    yield get_main_edition_link(info_tag)
    yield from get_other_edition_links(ex_info_tag)


def check_is_english_from_main(info_tag: Tag) -> bool:
    return info_tag.find("img")["alt"].lower() == "english"


def analyse_main_rules(info_tag: Tag, english: bool = None) \
        -> Tuple[Optional[str], Optional[Tuple[int, int]], Tuple[List[str], str, List[str]]]:
    if english is None:
        english = check_is_english_from_main(info_tag)
    line = info_tag.find("p")
    linestr = line.contents[0]
    m = re.match("^\s*(.*?),?\s*\n\s*(.*?)\s*(\n*\s*)?$", linestr)
    type_line = m.group(1)
    mana_string = m.group(2)
    mana = analyse_mana_string(mana_string)
    if not english:
        division = info_tag.find("div", class_="oo")
        type_line = division.find("span").string
        type_line = str(type_line).strip()
    type_line, pt = split_pt_from_type_line(type_line)
    super_types, main_type, sub_types = analyse_type_line(type_line)
    return mana, pt, (super_types, main_type, sub_types)


def _listify_mana(mana_string) -> Sequence[str]:
    mana_string = re.sub("(\s*\(\d+\))?$", "", mana_string)
    special = (s[1:-1] for s in re.findall(r"{[^}]*}", mana_string))
    mana_string = re.sub(r"{[^}]*}", "", mana_string)
    general = re.findall("\d+", mana_string)
    mana_string = re.sub("\d+", "", mana_string)
    allmana = itertools.chain(general, mana_string, special)
    return allmana


def analyse_mana_string(mana_string: str) -> Optional[List[mana_types.Mana]]:
    mana_string = mana_string.strip()
    if len(mana_string) == 0:
        return None
    cmc_list = _listify_mana(mana_string)
    tdict = Counter(cmc_list)
    t = []
    for n, c in tdict.items():
        try:
            t.append(mana_types.Mana.make_mana(n, c))
        except KeyError as e:
            logger.error("Unknown mana: {0}".format(n))
    return t


def split_pt_from_type_line(type_line: str) -> Tuple[str, Optional[Tuple[int, int]]]:
    v = re.match(r"^(.*?)\s*(\d+(?:\.\d+)?/\d+(?:\.\d+)?)?$", type_line)
    types = v.group(1)
    pt = None
    pt_str = v.group(2)
    if pt_str is not None:
        pt = tuple(map(int, pt_str.split("/", maxsplit=1)))
    return types, pt


def analyse_type_line(type_line: str) -> Tuple[List[str], str, List[str]]:
    t = re.split(r"\s*(?:-|—)+\s*", type_line, maxsplit=1)
    super_ = t[0]
    if len(t) > 1:
        sub = t[1]
    else:
        sub = ""
    super_main_list = super_.split()
    super_types = super_main_list[:-1]
    main_type = super_main_list[-1]
    sub_types = sub.split()
    return super_types, main_type, sub_types
