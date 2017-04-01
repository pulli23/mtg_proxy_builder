from bs4 import Tag
from typing import AnyStr, Optional

import card_downloader as card_dl
import mana_types
import requests


class Card:
    def __init__(self, name: AnyStr, edition: AnyStr = None,
                 collectors_number: int = None, language: str = "en"):
        self._name = name
        self._version = MTGSET_CODES.get(edition, edition)
        self._colnum = collectors_number
        self._language = language
        self._types = []
        self._subtypes = []
        self._supertypes = []
        self._pt = None
        self.mana = None

    def alike(self, other: "Card") -> bool:
        sv = self.edition
        ov = other.edition
        return (not sv or not ov or sv == ov) and self.name.lower() == other.name.lower()

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

    def load_extended_information(self, info_tag: Tag = None, session: requests.Session = None):
        if info_tag is None:
            _, info_tag, _ = card_dl.find_card_tablecells(self.name, self.edition,
                                                          self.collectors_number, self.language,
                                                          session=session)
        mana, pt, alltypes = card_dl.analyse_main_rules(info_tag)
        self.mana = mana
        self._pt = pt
        self._types = alltypes

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


def force_edition_and_number_copy(card: Card, session: requests.Session = None) -> Card:
    edition = card.edition
    num = card.collectors_number
    language = card.language
    if edition is None or num is None:
        url = next(card_dl.find_card_urls(card, session=session))
        edition, language, num = card_dl.analyse_hyperref(url)

    return Card(card.name, edition, num, language)


def make_fully_qualified_card_from_info(info_tag: Tag):
    url = card_dl.get_main_edition_link(info_tag)
    edition, language, collectors_number = card_dl.analyse_hyperref(url)
    name = card_dl.get_main_name(info_tag)
    card = Card(name, edition, int(collectors_number), language)
    return card


def make_fully_qualified_card(name: AnyStr = None, edition: AnyStr = None,
                              collectors_number: int = None, language: AnyStr = None):
    if name is None and (edition is None or collectors_number is None):
        raise ValueError("bad inputs")
    if language is None and name is None:
        language = "en"
    if edition is not None:
        edition = MTGSET_CODES.get(edition, edition)
    _, info_tag, _ = card_dl.find_card_tablecells(name, edition, collectors_number, language)
    return make_fully_qualified_card_from_info(info_tag)


def _make_mtgsetcode_array():
    codes = {
        "limit edition alpha": "lea",
        "limit edition beta": "leb",
        "unlimited edition": "2ed",
        "revised edition": "3ed",
        "fourth edition": "4ed",
        "fifth edition": "5ed",
        "classic sixth edition": "6ed",
        "seventh edition": "7ed",
        "eighth edition": "8ed",
        "ninth edition": "9ed",
        "tenth edition": "10e",
        "magic 2010": "m10",
        "magic 2011": "m11",
        "magic 2012": "m12",
        "magic 2013 core set": "m13",
        "magic 2014 core set": "m14",
        "magic origins": "ori",

        "arabian nights": "arn",
        "antiquities": "atq",
        "legends": "leg",
        "the dark": "drk",
        "fallen empires": "fem",
        "homelands": "hml",
        "ice age": "ice",
        "alliances": "all",
        "coldsnap": "csp",
        "mirage": "mir",
        "visions": "vis",
        "weatherlight": "wth",
        "tempest": "tmp",
        "stronghold": "sth",
        "exodus": "exo",
        "urza's sage": "usg",
        "urza's legacy": "ulg",
        "urza's destiny": "uds",
        "mercadian masques": "mmq",
        "nemesis": "nem",
        "prophecy": "pcy",
        "invasion": "inv",
        "planeshift": "pls",
        "apocalypse": "apc",
        "odyssey": "ody",
        "torment": "tor",
        "judgement": "jud",
        "onslaught": "ons",
        "legions": "lgn",
        "scourge": "scg",
        "mirrodin": "mrd",
        "darksteel": "dst",
        "fifth dawn": "5dn",
        "champions of kamigawa": "chk",
        "betrayers of kamigawa": "bok",
        "saviors of kamigawa": "sok",
        "ravnica: city of guilds": "rav",
        "guildpact": "gpt",
        "dissension": "dis",
        "time spiral": "tsp",
        "planar chaos": "plc",
        "future sight": "fut",
        "lorwyn": "lrw",
        "morningtide": "mor",
        "shadowmoor": "shm",
        "eventide": "eve",
        "shards of alara": "ala",
        "conflux": "con",
        "alara reborn": "arb",
        "zendikar": "zen",
        "worldwake": "wwk",
        "rise of the eldrazi": "roe",
        "scars of mirrodin": "som",
        "mirrodin besieged": "mbs",
        "new phyrexia": "nph",
        "innistrad": "isd",
        "dark scension": "dka",
        "avacyn restored": "avr",
        "return to ravnica": "rtr",
        "gatecrash": "gtc",
        "dragon's maze": "dgm",
        "theros": "ths",
        "born of the gods": "bng",
        "journey into nyx": "jou",
        "khans of tarkir": "ktk",
        "fater reforged": "frf",
        "dragons of tarkir": "dtk",
        "battle for zendikar": "bfz",
        "oath of the gatewatch": "ogw",
        "shadows over innistrad": "soi",
        "eldritch moon": "emn",
        "kaladesh": "kld",
        "aether revolt": "aer",
        "amonkhet": "akh",
        "hour of devastation": "hou",

        "chronicles": "chr",
        "anthologies": "ath",
        "battle royale box set": "brb",
        "beatdown box set": "btd",
        "deckmasters: garfield vs. finkel": "dkm",
        "eternal masters": "ema",
        "duel decks: elves vs. goblins": "evg",
        "duel decks: jace vs. chandra": "dd2",
        "duel decks: divine vs. demonic": "ddc",
        "duel decks: garruk vs. liliana": "ddd",
        "duel decks: phyrexia vs. the coalition": "dde",
        "duel decks: elspeth vs. tezzeret": "ddf",
        "duel decks: knights vs. dragons": "ddg",
        "duel decks: ajani vs. nicol bolas": "ddh",
        "duel decks: venser vs. koth": "ddi",
        "duel decks: izzet vs. golgari": "ddj",
        "duel decks: sorin vs. tibalt": "ddk",
        "duel decks: heroes vs. monsters": "ddl",
        "duel decks: jace vs. vraska": "ddm",
        "duel decks: speed vs. cunning": "ddn",
        "duel decks anthology": "dd3",
        "duel decks: elspeth vs. kiora": "ddo",
        "duel decks: zendikar vs. eldrazi": "ddp",
        "duel decks: blessed vs. cursed": "ddq",
        "duel decks: nissa vs. ob nixilis": "ddr",
        "duel decks: mind vs might": "dds",
        "from the vault: dragons": "drb",
        "from the vault: exiled": "v09",
        "from the vault: relics": "v10",
        "from the vault: legends": "v11",
        "from the vault: realms": "v12",
        "from the vault: twenty": "v13",
        "from the vault: annihilation": "v14",
        "from the vault: angels": "v15",
        "from the vault: lore": "v16",
        "premium deck series: slivers": "h09",
        "premium deck series: fire and lightning": "pd2",
        "premium deck series: graveborn": "pd3",
        "modern masters": "mma",
        "modern masters 2015 edition": "mm2",
        "modern masters 2017 edition": "mm3",
        "modern event deck 2014": "md1",

        "planechase": "hop",
        "planechase 2012 edition": "pc2",
        "planechase anthology": "pca",
        "archenemy": "arc",
        "commander": "cmd",
        "commander's arsenal": "cma",
        "commander 2013 edition": "c13",
        "commander 2014": "c14",
        "commander 2015": "c15",
        "commander 2016": "c16",
        "conspiracy": "cns",
        "conspiracy: take the crown": "cn2",

        "portal": "por",
        "portal second age": "po2",
        "portal three kingdoms": "ptk",
        "starter 1999": "s99",
        "starter 2000": "s00",

        "collector's edition": "ced",
        "international collector's edition": "ced",
        "unglued": "ugl",
        "unhinged": "unh"
    }
    __append = {v: v for v in codes.values()}
    codes.update(__append)
    __append = {
        "al": "lea",
        "be": "leb",
        "un": "2ed",
        "rv": "3ed",
        "4e": "4ed",
        "5e": "5ed",
        "6e": "5ed",
        "7e": "7ed",
        "8e": "7ed",
        "9e": "7ed",
        "an": "arn",
        "aq": "atq",
        "lg": "leg",
        "dk": "drk",
        "fe": "fem",
        "hl": "hml",
        "ia": "ice",
        "ai": "all",
        "cstd": "csp",
        "cs": "csp",
        "mr": "mir",
        "vi": "vis",
        "wl": "wth",
        "tp": "tmp",
        "sh": "sth",
        "ex": "exo",
        "us": "usg",
        "ul": "ulg",
        "ud": "uds",
        "mm": "mmq",
        "ne": "nem",
        "pr": "pcy",
        "in": "inv",
        "ps": "pls",
        "ap": "apc",
        "od": "ody",
        "tr": "tor",
        "ju": "jud",
        "on": "ons",
        "le": "lgn",
        "sc": "scg",
        "mi": "mrd",
        "ds": "dst",
        "gp": "gpt",
        "di": "dis",
        "ts": "tsp",
        "pc": "plc",
        "lw": "lrw",
        "mt": "mor",
        "cfx": "con",

        "ch": "chr",
        "at": "ath",
        "br": "brb",
        "bd": "btd",
        "dm": "dkm",
        "jvc": "dd2",
        "dvd": "ddc",
        "gvl": "ddd",
        "pvc": "dde",
        "fvd": "drb",
        "fve": "v09",
        "fvr": "v10",
        "fvl": "v11",
        "pds": "h09",

        "pch": "hop",

        "po": "por",
        "p3k": "ptk",
        "st": "s99",
        "st2k": "s00",

        "cedi": "ced",
        "ug": "ugl",
        "uh": "unh"
    }
    codes.update(__append)
    # synonyms
    __append = {
        "alpha": "lea",
        "beta": "leb",
        "sixth edition": "6ed",
        "magic 2013": "m13",
        "magic 2014": "m14",
        "ravnica": "rav",
        "third edition": "3ed",
        "3rd edition": "3ed",
        "4th edition": "4ed",
        "5th edition": "5ed",
        "6th edition": "6ed",
        "7th edition": "7ed",
        "8th edition": "8ed",
        "9th edition": "9ed",
        "10th edition": "10e",
        "origins": "ori",
        "deckmasters": "dkm",
        "commander anthology": "cma"
    }
    codes.update(__append)
    __append = {}
    for _name, _short in codes.items():
        t = " edition"
        if _name.endswith(t) and len(_name) > len(t):
            __append[_name[:-len(t)]] = _short
    codes.update(__append)
    __append = {}
    for __name, _short in codes.items():
        ex = "Prerelease Events: "
        dd = "duel decks: "
        ftv = "from the vault: "
        if __name.startswith(dd) and len(__name) > len(dd):
            __append[__name[len(dd):]] = _short
        elif __name.startswith(ftv) and len(__name) > len(ftv):
            __append["ftv: " + __name[len(ftv):]] = _short
        else:
            __append[ex + __name] = _short
    codes.update(__append)
    codes.update(__append)

    codes = {n.lower(): v.lower() for n, v in codes.items()}
    return codes



MTGSET_CODES = _make_mtgsetcode_array()
