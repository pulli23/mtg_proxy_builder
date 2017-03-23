import io
import itertools
import typing
from typing import Iterable
from typing import Optional, Callable, List, Tuple, Dict

from card import Card
from proxybuilder_types import CardListTy


def save_file(outstream: typing.io.TextIO, mainboard: CardListTy, sideboard: CardListTy,
              card_process: Callable[[Card, int, bool], str]):
    mainboard = ((card, num, True) for card, num in mainboard)
    sideboard = ((card, num, False) for card, num in sideboard)
    longlist = itertools.chain(mainboard, sideboard)
    for card, count, sec in longlist:
        line = card_process(card, count, sec)
        outstream.write(line)


class WriteHandleTextLine:
    def __init__(self, mb_check: str = "mainboard",
                 sb_check: str = "sideboard"):
        self.check = {True: mb_check, False: sb_check}
        self.current_section = None  # type: bool

    def __call__(self, card: Card, count: int, section: bool) -> str:
        line = ""
        if self.current_section is None or section != self.current_section:
            line += self.check[section]
            self.current_section = section
        if card.version:
            line += "{0} {1}".format(count, card.name)
        else:
            line += "{0} {1} [{2}]".format(count, card.name, card.version)
        return line


def save_txt(outstream: typing.io.TextIO, mainboard: CardListTy, sideboard: CardListTy) -> None:
    card_processor = WriteHandleTextLine()
    save_file(outstream, mainboard, sideboard, card_processor)


def save_csv(outstream: typing.io.TextIO, mainboard: CardListTy, sideboard: CardListTy) -> None:
    pass


def save_xmage(outstream: typing.io.TextIO, mainboard: CardListTy, sideboard: CardListTy) -> None:
    pass