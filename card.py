from typing import AnyStr, Optional, Tuple, Generator, Dict, List, Union

import card_downloader as card_dl
import mana_types
from card_set_codes import get_mtgset_codes
from export.jsonencoders import JSONable


class Card(JSONable):
    def to_json(self) -> Dict[str, str]:
        d = super().to_json()
        d.update({"name": self.name,
                  "edition": self.edition,
                  "language": self.language,
                  "collectors_number": self.collectors_number,
                  "_supertypes": self._supertypes,
                  "_types": self._types,
                  "_subtypes": self._subtypes,
                  "mana": self.mana_string(),
                  "pt": self._pt})
        return d

    @classmethod
    def from_json(cls, _supertypes, _types, _subtypes, mana, pt, **kwargs) -> "Card":
        newcard = cls(**kwargs)
        newcard._supertypes = _supertypes
        newcard._types = _types
        newcard._subtypes = _subtypes
        newcard.mana = mana
        if pt is None:
            newcard._pt = pt
        else:
            newcard._pt = tuple(pt)
        return newcard

    def __init__(self, name: AnyStr, edition: AnyStr = None,
                 collectors_number: int = None, language: str = None, side_num: List[str] = None, **kwargs):
        self._name = name.lower()
        self._version = get_mtgset_codes().get(edition, edition)
        self._colnum = collectors_number
        self._language = language
        self._types = []
        self._subtypes = []
        self._supertypes = []
        self._pt = None
        self._mana = None
        self.card_side_num = side_num
        if side_num is None:
            self.card_side_num = []

    def alike(self, other: "Card") -> bool:
        sv = self.edition
        ov = other.edition
        sl = self.language
        ol = other.language
        return (not sv or not ov or sv == ov) and \
               (not sl or not ol or sl == ol) and \
               self.name == other.name

    @property
    def language(self) -> str:
        return self._language

    @property
    def name(self) -> str:
        return self._name

    @property
    def edition(self) -> str:
        return self._version

    @property
    def power(self) -> int:
        return None if self._pt is None else self._pt[0]

    @property
    def thoughness(self) -> int:
        return None if self._pt is None else self._pt[1]

    @property
    def cmc(self) -> Optional[int]:
        if self.mana is None:
            return None
        else:
            return sum(type(m).effective_cost * m.number for m in self.mana)

    @property
    def collectors_number(self) -> int:
        return self._colnum

    @property
    def mana(self):
        return self._mana

    @mana.setter
    def mana(self, mana_string: str):
        self._mana = mana_types.analyse_mana_string(mana_string)

    def __eq__(self, other: "Card") -> bool:
        return isinstance(other, self.__class__) \
               and self.name == other.name \
               and self.edition == other.edition \
               and self.collectors_number == other.collectors_number \
               and self.language == other.language

    def __hash__(self) -> int:
        return hash((self.name, self.edition, self.collectors_number, self.language))

    def __str__(self) -> str:
        if self.edition == "":
            return self.name
        else:
            return "{0} [{1}]".format(self.name, self.edition)

    def __repr__(self) -> str:
        return "{0}(name={1}, edition={2}, collectors_number={3}, language={4})" \
            .format(type(self).__name__,
                    self.name,
                    self.edition,
                    self.collectors_number,
                    self.language)

    def load_extended_information(self, analyzed_html: card_dl.HTMLAnalyzer):
        mana, pt, alltypes = analyzed_html.analyse_main_rules()
        self.mana = mana
        self._pt = pt
        self._supertypes = alltypes[0]
        self._subtypes = alltypes[2]
        self._types = alltypes[1]

    def mana_string(self) -> str:
        if self.mana is None:
            return ""
        if len(self.mana) == 0:
            return "0"
        types = {type(m): m for m in self.mana}
        gen = ""
        if mana_types.GenericMana in types:
            gen = str(types[mana_types.GenericMana])
        return gen + ''.join(str(m) for m in self.mana if type(m) != mana_types.GenericMana)

    def magiccards_info_number_list(self) -> Generator[str, None, None]:
        colnum = str(self.collectors_number)
        return (colnum + idx for idx in self.card_side_num)

    def __lt__(self, other):
        return (self.name,
                self.edition if self.edition is not None else "",
                self.language if self.language is not None else "") \
               < (other.name,
                  other.edition if other.edition is not None else "",
                  other.language if other.language is not None else "")

    def is_specific(self, other: "Card") -> bool:
        sv = self.edition
        ov = other.edition
        sl = self.language
        ol = other.language
        return (not ov or sv == ov) and \
               (not ol or sl == ol) and \
               self.name == other.name


def force_edition_and_number_copy(card: Card, session: card_dl.CardDownloader = None) -> Card:
    if session is None:
        session = card_dl.CardDownloader()
    analyzer = session.make_html_analyzer(card.name, card.edition, next(card.magiccards_info_number_list()),
                                          card.language)
    edition = card.edition
    num = card.collectors_number
    language = card.language
    parts = card.card_side_num
    if not edition or not num:
        url = next(analyzer.find_card_urls())
        edition, language, num, other_part = card_dl.analyse_hyperref(url)

    return Card(analyzer.get_main_name(), edition, num, language, parts)


def make_fully_qualified_card_from_info(analyzer: card_dl.HTMLAnalyzer) -> Card:
    url = analyzer.get_main_edition_link()
    edition, language, collectors_number, is_double = card_dl.analyse_hyperref(url)
    name = analyzer.get_main_name()
    card = Card(name, edition, int(collectors_number), language, is_double)
    return card


def make_fully_qualified_card(name: AnyStr = None, edition: AnyStr = None,
                              collectors_number: str = None, language: AnyStr = None,
                              session: card_dl.CardDownloader = None) -> Card:
    if name is None and (edition is None or collectors_number is None):
        raise ValueError("bad inputs")
    if session is None:
        session = card_dl.CardDownloader()
    if language is None and name is None:
        language = "en"
    if edition is not None:
        edition = get_mtgset_codes().get(edition, edition)
    analyzer = session.make_html_analyzer(name, edition, collectors_number, language)
    return make_fully_qualified_card_from_info(analyzer)
