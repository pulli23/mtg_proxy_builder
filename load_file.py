import os
import csv
import io
from typing import Optional, Callable, List, Tuple, Any, TypeVar, Callable, Iterable
import itertools
import operator
import re

from card import Card

CardCountTy = Tuple[Card, int]







def read_file(file: Iterable, line_process: Callable[[], Optional[Tuple[Card, int, bool]]], *args, **kwargs) \
        -> Tuple[List[CardCountTy], List[CardCountTy]]:
    inputlist = (line_process(row, *args, **kwargs) for row in file)
    inputlist = list(filter(None, inputlist))
    t = tuple([i[:2] for i in group]
              for key, group in itertools.groupby(inputlist, operator.itemgetter(2)))
    return t


def process_deckbox_deck_row(row: Tuple[str, ...]) -> Optional[Tuple[Card, int, bool]]:
    try:
        return Card(row[1].lower()), int(row[0]), True if row[2].lower() == "main" else False
    except (ValueError, IndexError):
        return None


def process_deckbox_inventory_row(row: Tuple[str, ...]) -> Optional[CardCountTy]:
    try:
        return Card(row[2].lower(), row[3].lower()), int(row[0])
    except (ValueError, IndexError):
        return None


def read_inventory_deckbox_org(file: io.IOBase, delimiter: str = ',', quotechar: str = '"') \
        -> List[CardCountTy]:
    csvreader = csv.reader(file, delimiter=delimiter, quotechar=quotechar)
    inputlist = list(process_deckbox_inventory_row(row) for row in csvreader)
    inputlist = list(filter(None, inputlist))
    return inputlist


def read_csv(file: io.IOBase, delimiter: str = ',', quotechar: str = '"') \
        -> Tuple[List[CardCountTy], List[CardCountTy]]:
    csvreader = csv.reader(file, delimiter=delimiter, quotechar=quotechar)
    return read_file(csvreader, process_deckbox_deck_row)


class HandleTextline:
    def __init__(self, mb_check: Optional[str] = r"main(\s*(board|deck))?\s*([([{<]\d+[]>})]\s*)?:?",
                 sb_check: Optional[str] = r"^side(\s*board)?\s*([([{]\d+[]})]\s*)?:?",
                 line_check: Optional[str] = None):
        if line_check is None:
            version_part = r"\[[^]]+?\]"
            name_part = r"[^]0-9[\s](?:[^]0-9[]*[^]0-9[\s])?"
            line_check = r"(\d+)\s+(({0})\s+({1})|({1})\s+({0})|({0}))".format(name_part, version_part)
        self.prog_line = re.compile(line_check, re.IGNORECASE)
        self.prog_main = re.compile(mb_check, re.IGNORECASE)
        self.prog_side = re.compile(sb_check, re.IGNORECASE)

        self.loading_main = True

    def __call__(self, line: str) -> Optional[Tuple[Card, int, bool]]:
        line = line.strip()
        if re.match(self.prog_main, line) is None:
            if re.match(self.prog_side, line) is None:
                mo = re.fullmatch(self.prog_line, line)
                if mo is not None:
                    num = int(mo.group(1))
                    if mo.group(3) is None:
                        if mo.group(6) is None:
                            name = mo.group(7)
                            version = ""
                        else:
                            name = mo.group(6)
                            version = mo.group(5)[1:-1]
                    else:
                        name = mo.group(3)
                        version = mo.group(4)[1:-1]
                    return Card(name, version), num, self.loading_main
            else:
                self.loading_main = False
        else:
            self.loading_main = True
        return None


def read_txt(file: io.IOBase) \
        -> Tuple[List[CardCountTy], List[CardCountTy]]:
    line_reader = HandleTextline()
    return read_file(file, line_reader)


class HandleXmageLine:
    def __init__(self, line_check: Optional[str] = None):
        if line_check is None:
            version_part = r"\[([\d\w]{3}):\d+\]"
            name_part = r"[^]0-9[\s](?:[^]0-9[]*[^]0-9[\s])?"
            line_check = r"(SB:)?\s*(\d+)\s*({1})\s\s*({0})".format(name_part, version_part)
        self.prog_line = re.compile(line_check, re.IGNORECASE)

    def __call__(self, line: str) -> Optional[Tuple[Card, int, bool]]:
        line = line.strip().lower()
        mo = re.fullmatch(self.prog_line, line)
        if mo is not None:
            sb = True if mo.group(1) is not None else False
            num = int(mo.group(2))
            name = mo.group(5)
            version = mo.group(4)
            return Card(name, version), num, sb

        return None


def read_xmage_deck(file: io.IOBase) \
        -> Tuple[List[CardCountTy], List[CardCountTy]]:
    line_reader = HandleXmageLine()
    return read_file(file, line_reader)