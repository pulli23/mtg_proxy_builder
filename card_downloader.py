import os
import requests
import difflib
import re
import functools
from typing import List, Tuple, Iterable, Generator, Dict, Optional
from card_set_codes import get_mtgset_codes

from bs4 import BeautifulSoup, Tag

import mylogger
import mana_types

logger = mylogger.MAINLOGGER


def fix_magiccards_info_code(shortcode: str) -> str:
    codes = {
        "nem": "ne"
    }
    return codes.get(shortcode, shortcode)


class HTMLAnalyzer:
    @staticmethod
    def _make_soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html5lib")

    @staticmethod
    def pick_best_matching_card(name: str, card_info_seq: Iterable[Tuple[Tag, Tag, Tag]]) \
            -> Tuple[Tag, Tag, Tag]:
        def get_relative_match(match: str):
            return difflib.SequenceMatcher(None, match.lower(), name.lower()).ratio()

        try:
            return max(card_info_seq,
                       key=lambda x: get_relative_match(next(x[1].find("a").stripped_strings)))
        except ValueError:
            raise ValueError("card '{0}' not found".format(name))

    @staticmethod
    def unpack_cardtable(cardtable) -> Tuple[Tag, Tag, Tag]:
        search = cardtable
        tb = search.find("tbody", recursive=False)
        if tb is not None:
            search = tb
        tr = search.find("tr", recursive=False)
        if tr is not None:
            search = tr
        img, info, ex_info, *residu = search.find_all("td", recursive=False)
        return img, info, ex_info

    @classmethod
    def safe_unpack_cardtables(cls, cardtables: Iterable[Tag]) \
            -> Generator[Tuple[Tag, Tag, Tag], None, None]:
        for table in cardtables:
            try:
                yield cls.unpack_cardtable(table)
            except StopIteration:
                pass

    def __init__(self, html: str, cardname: str = None):
        self._soup = type(self)._make_soup(html)
        self._cardname = cardname
        self._info_tag = None  # type:Optional[Tag]
        self._img_tag = None  # type:Optional[Tag]
        self._ex_info_tag = None  # type:Optional[Tag]
        self._is_english = None  # type:Optional[bool]

    def _find_and_unpack_best_card_table(self) -> Tuple[Tag, Tag, Tag]:
        cardtables = self.find_htmltext_tables()
        card_info_list = self.safe_unpack_cardtables(cardtables)
        if self._cardname is not None:
            return type(self).pick_best_matching_card(self._cardname, card_info_list)
        else:
            return next(card_info_list)

    def find_htmltext_tables(self) -> List[Tag]:
        v = self._soup.find_all('table')
        v = [tab for tab in v if len(tab.find_all('a')) > 0
             and len(tab.find_all('img')) > 0
             and (not tab.has_attr("id") or tab["id"] != "nav")]
        return v

    @property
    def info_tag(self) -> Tag:
        if self._info_tag is None:
            tup = self._find_and_unpack_best_card_table()  # type: Tuple[Tag, Tag, Tag]
            self._img_tag, self._info_tag, self._ex_info_tag = tup
        return self._info_tag

    @property
    def ex_info_tag(self) -> Tag:
        if self._ex_info_tag is None:
            tup = self._find_and_unpack_best_card_table()
            self._img_tag, self._info_tag, self._ex_info_tag = tup
        return self._ex_info_tag

    @property
    def img_tag(self) -> Tag:
        if self._img_tag is None:
            tup = self._find_and_unpack_best_card_table()
            self._img_tag, self._info_tag, self._ex_info_tag = tup
        return self._img_tag

    @property
    def is_english(self) -> bool:
        if self._is_english is None:
            self._is_english = self.check_is_english_from_main()
        # noinspection PyTypeChecker
        return self._is_english

    def check_is_english_from_main(self) -> bool:
        return self.info_tag.find("img")["alt"].lower() == "english"

    def analyse_main_rules(self) \
            -> Tuple[str,
                     Optional[Tuple[int, int]],
                     Tuple[List[str], List[str], List[str]]]:
        cls = type(self)
        english = self.is_english
        info_tag = self.info_tag
        line = info_tag.find("p")
        linestr = line.contents[0]
        m = re.match("^\s*(.*?),?\s*\n\s*(.*?)\s*(\n*\s*)?$", linestr)
        type_line = m.group(1)
        mana_string = m.group(2)
        mana_string = mana_string.strip()  # strip whitespace from mana string
        mana_string = re.sub("(\s*\(\d+\))?$", "", mana_string)  # remove cmc value
        if not english:
            division = info_tag.find("div", class_="oo")
            type_line = division.find("span").string
            type_line = str(type_line).strip()
        type_line, pt = cls._split_pt_from_type_line(type_line)
        super_types, main_types, sub_types = cls._analyse_type_line(type_line)
        return mana_string, pt, (super_types, main_types, sub_types)

    def get_other_edition_links(self) -> Generator[str, None, None]:
        tag = self.ex_info_tag
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

    def get_main_edition_link(self) -> str:
        return self.info_tag.find("a")["href"]

    def get_main_name(self) -> str:
        return self.info_tag.find("a").string


    @staticmethod
    def _split_pt_from_type_line(type_line: str) -> Tuple[str, Optional[Tuple[int, int]]]:
        v = re.match(r"^(.*?)\s*(\d+(?:\.\d+)?/\d+(?:\.\d+)?)?$", type_line)
        types = v.group(1)
        pt = None
        pt_str = v.group(2)
        if pt_str is not None:
            pt = tuple(map(int, pt_str.split("/", maxsplit=1)))
        return types, pt

    @staticmethod
    def _analyse_type_line(type_line: str) -> Tuple[List[str], List[str], List[str]]:
        all_super_types = {
            "basic", "elite", "legendary", "ongoing", "snow", "world"
        }
        t = re.split(r"\s*(?:[-—])+\s*", type_line, maxsplit=1)
        super_ = t[0]
        if len(t) > 1:
            sub = t[1]
        else:
            sub = ""
        super_main_list = super_.split()
        super_types = []
        main_types = []
        for t in super_main_list:
            if t.lower() in all_super_types:
                super_types.append(t)
            else:
                main_types.append(t)
        sub_types = sub.split()
        return super_types, main_types, sub_types

    def find_card_urls(self) \
            -> Generator[str, None, None]:
        yield self.get_main_edition_link()
        yield from self.get_other_edition_links()

    def get_all_editions(self) -> Generator[Tuple[str, str, str], None, None]:
        urls = self.find_card_urls()
        card_infos = (analyse_hyperref(url) for url in urls)
        return ((get_mtgset_codes().get(edition, edition), lan, colnum) for edition, lan, colnum in card_infos)


def analyse_hyperref(href: str) -> Tuple[str, str, str]:
    htmllink = os.path.splitext(href)[0]
    edition, language, number = htmllink.strip('/.').split(sep='/')
    return edition, language, number





class CardDownloader:
    def __init__(self, source: str = "http://magiccards.info"):
        self.session = requests.session()
        self.source = source

    @functools.lru_cache(maxsize=512)
    def load_magic_card(self, name: str = None, edition: str = None,
                        collectors_number: int = None, language: str = None) \
            -> requests.Response:
        if self.session is None:
            session = requests
        else:
            session = self.session
        if name is None and (edition or collectors_number is not None or language):
            raise ValueError("Bad inputs")
        if edition and collectors_number is not None and language:
            url, payload = self._get_literal_url(edition, language, collectors_number)
        else:
            url, payload = self._get_lookup_url(name, edition, language)

        res = session.get(url, params=payload)
        logger.debug("Lookup url: {0}".format(res.url))
        res.raise_for_status()
        return res

    def _get_literal_url(self, edition: str, language: str, collectors_number: int) \
            -> Tuple[str, Dict[str, str]]:
        url = "{0}/{1}.html".format(self.source, '/'.join((fix_magiccards_info_code(edition),
                                                           language, str(collectors_number))))
        payload = {}
        return url, payload

    def _get_lookup_url(self, name: str, edition: str = None, language: str = None) \
            -> Tuple[str, Dict[str, str]]:
        name = name.replace('//', '/')
        if edition:
            name += " e:\"{0}\"".format(edition)
            if language:
                name += "/{0}".format(language)
        payload = {'q': name}
        url = self.source + "/query"
        return url, payload

    def make_html_analyzer(self, name: str = None, edition: str = None,
                           collectors_number: int = None, language: str = None) \
            -> HTMLAnalyzer:
        res = self.load_magic_card(name, edition, collectors_number, language)
        analyser = HTMLAnalyzer(res.text, cardname=name)
        return analyser
