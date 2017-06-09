import io
import itertools
import typing
import os
from typing import Iterable
from typing import Optional, Callable, List, Tuple, Dict
import requests

import card
from card import Card
from proxybuilder_types import CardListTy, CardIterTy
import card_downloader as cdl
from export.jsonencoders import dump_string, dump_file
import mylogger

logger = mylogger.MAINLOGGER


def save_file(outstream: typing.TextIO, mainboard: CardIterTy, sideboard: CardIterTy,
              card_process: Callable[[Card, int, bool], str]):
    mainboard = ((c, num, True) for c, num in mainboard)
    sideboard = ((c, num, False) for c, num in sideboard)
    longlist = itertools.chain(mainboard, sideboard)
    longlist = list(longlist)
    for c, count, sec in longlist:
        line = card_process(c, count, sec)
        outstream.write(line)


class WriteHandleTextLine:
    def __init__(self, mb_check: str = "mainboard",
                 sb_check: str = "sideboard"):
        self.check = {True: mb_check, False: sb_check}
        self.current_section = None  # type: bool

    def __call__(self, card: Card, count: int, section: bool) -> str:
        line = ""
        if self.current_section is None or section != self.current_section:
            line += self.check[section] + '\n'
            self.current_section = section
        if not card.edition:
            line += "{0} {1}\n".format(count, card.name)
        else:
            line += "{0} {1} [{2}]\n".format(count, card.name, card.edition)
        return line


def save_txt(outstream: typing.TextIO, mainboard: CardListTy, sideboard: CardListTy, name: str = None) -> None:
    card_processor = WriteHandleTextLine()
    save_file(outstream, mainboard, sideboard, card_processor)


class WriteHandleCSVLine:
    def __init__(self):
        self.order = ["Count", "Name", "Type", "Price", "Section"]


def save_csv(outstream: typing.TextIO, mainboard: CardListTy, sideboard: CardListTy, name: str = None) -> None:
    pass


class WriteHandleXMageLine:
    unsupported_sets = {
        "pca", "brb"
    }
    unsupported_cards = {}

    def __init__(self, name: str = None, session: cdl.CardDownloader = None):
        self.name = name
        self.first_line = False

        if session is None:
            session = cdl.CardDownloader()
        self.session = session

    def __call__(self, c: Card, count: int, section: bool) -> str:
        line = ""
        analyzer = None
        if not self.first_line:
            line += "NAME:{0}\n".format(self.name)
            self.first_line = True
        if not section:
            line += "SB: "
        if c.edition.lower() in self.unsupported_sets:
            if analyzer is None:
                analyzer = self.session.make_html_analyzer(c.name, c.edition, next(c.magiccards_info_number_list()), c.language)
            try:
                ed, lan, n, is_double = next((ed, lan, n, is_double)
                                             for ed, lan, n, is_double in analyzer.get_all_editions()
                                             if ed not in self.unsupported_sets)
                old_card = c
                c = Card(old_card.name, ed, n, lan, is_double)
                logger.warning("Set unsupported, card: {0}".format(old_card),
                               verbose_msg="New card: {0}".format(c))
            except StopIteration:
                logger.error("Set unsupported, card: {0} - no working version".format(old_card))
                raise
        line += "{0} [{1}:{2}] {3}\n".format(count, c.edition.upper(), c.collectors_number, c.name)
        return line


def _check_and_force_edition_num(c: Card, session: cdl.CardDownloader = None):
    if c.name and c.collectors_number and c.edition:
        return c
    else:
        return card.force_edition_and_number_copy(c, session)


def save_xmage(outstream: typing.TextIO, mainboard: CardListTy, sideboard: CardListTy, name: str = None) -> None:
    session = cdl.CardDownloader()
    newmainboard = ((_check_and_force_edition_num(c, session), n) for c, n in mainboard)
    newsideboard = ((_check_and_force_edition_num(c, session), n) for c, n in sideboard)
    if not name:
        name = os.path.splitext(os.path.split(outstream.name)[-1])[0]
    card_processor = WriteHandleXMageLine(name)
    save_file(outstream, newmainboard, newsideboard, card_processor)


def save_json(outstream: typing.TextIO, mainboard: CardIterTy, sideboard: CardListTy, name: str = None) -> None:
    d = {"mainboard": [(c, n) for c, n in mainboard], "sideboard": [(c, n) for c, n in sideboard], "name": name}
    dump_file(d, outstream)
