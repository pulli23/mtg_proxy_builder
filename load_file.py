import csv
import io
import _io
from typing import Optional, Callable, List, Tuple, Any, TypeVar, Callable, Iterable, Sequence
import itertools
import operator
import re

from card import Card

CardCountTy = Tuple[Card, int]
CardCountSecTy = Tuple[Card, int, bool]
CardListTy = List[CardCountTy]


def read_file(file: Iterable, line_process: Callable[[], Optional[CardCountSecTy]], *args, **kwargs) \
        -> Tuple[CardListTy, CardListTy]:
    inputlist = (line_process(row, *args, **kwargs) for row in file)
    inputlist = list(filter(None, inputlist))
    t = tuple([i[:2] for i in group]
              for key, group in itertools.groupby(inputlist, operator.itemgetter(2)))
    if len(t) < 2:
        return t[0], []
    return t[0], t[1]


def process_deckbox_deck_row(row: Tuple[str, ...]) -> Optional[CardCountSecTy]:
    try:
        return Card(row[1].lower()), int(row[0]), True if row[2].lower() == "main" else False
    except (ValueError, IndexError):
        return None


def process_csv_row(row: Tuple[str, ...], name_column: int, count_column: int,
                    version_column: Optional[int]=None, section_column: Optional[int]=None) \
        -> Optional[CardCountSecTy]:
    try:
        v = row[version_column].lower() if version_column is not None else ""
        s = True if section_column is None or row[section_column].lower() == "main" else False
        c = Card(row[name_column].lower(), v)
        n = int(row[count_column])
        return c, n, s
    except (ValueError, IndexError):
        return None


def process_deckbox_inventory_row(row: Tuple[str, ...]) -> Optional[CardCountTy]:
    try:
        return Card(row[2].lower(), row[3].lower()), int(row[0])
    except (ValueError, IndexError):
        return None


def read_inventory_deckbox_org(file: io.IOBase, *args, **kwargs) \
        -> CardListTy:
    return read_csv(file, name_column=2, count_column=0,
                    section_column=None, version_column=3,
                    *args, **kwargs)[0]


def read_csv(file: io.IOBase, name_column:int=1, count_column:int=0,
             section_column:Optional[int]=2, version_column:Optional[int]=None, *args, **kwargs) \
        -> Tuple[CardListTy, CardListTy]:
    csvreader = csv.reader(file, *args, **kwargs)
    return read_file(csvreader, lambda line: process_csv_row(line,
                                                             name_column,
                                                             count_column,
                                                             version_column=version_column,
                                                             section_column=section_column
                                                             ))


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

    def sniff(self, line: str) -> bool:
        line = line.strip()
        if line and \
            re.match(self.prog_main, line) is None and \
            re.match(self.prog_side, line) is None and \
            re.fullmatch(self.prog_line, line) is None:
            return False
        else:
            return True

    def __call__(self, line: str) -> Optional[CardCountSecTy]:
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


def read_txt(file: io.IOBase, line_reader: Optional[Callable[[str], Optional[CardCountSecTy]]] = None) \
        -> Tuple[CardListTy, CardListTy]:
    if line_reader is None:
        line_reader = HandleTextline()
    return read_file(file, line_reader)


class HandleXmageLine:
    def __init__(self, line_check: Optional[str] = None):
        if line_check is None:
            version_part = r"\[([\d\w]{3}):\d+\]"
            name_part = r"[^]0-9[\s](?:[^]0-9[]*[^]0-9[\s])?"
            line_check = r"(SB:)?\s*(\d+)\s*({1})\s\s*({0})".format(name_part, version_part)
        self.prog_line = re.compile(line_check, re.IGNORECASE)

    def get_match_object(self, line:str):
        line = line.strip().lower()
        mo = re.fullmatch(self.prog_line, line)
        return mo

    def __call__(self, line: str) -> Optional[CardCountSecTy]:
        mo = self.get_match_object(line)
        if mo is not None:
            sb = True if mo.group(1) is not None else False
            num = int(mo.group(2))
            name = mo.group(5)
            version = mo.group(4)
            return Card(name, version), num, sb
        return None


def read_xmage_deck(file: io.IOBase, line_reader: Optional[Callable[[str], Optional[CardCountSecTy]]] = None) \
        -> Tuple[CardListTy, CardListTy]:
    if line_reader is None:
        line_reader = HandleXmageLine()
    return read_file(file, line_reader)


def sniff_xmage(sample: Sequence) -> Callable[[str], Optional[CardCountSecTy]]:
    midlines = HandleXmageLine()
    firstline = HandleXmageLine("name:.*")
    version_part = r"\[([\d\w]{3}):\d+\]"
    layout_regex = r"\(\d+,\d+\)\([\w_]+,(true|false)(,\d+)?\)\|(\(({0}(,{0})*)?\))*".format(version_part)
    last_lines = HandleXmageLine("layout (main|sideboard):" + layout_regex)
    match_order = [firstline, midlines, last_lines]
    current = 0
    for line in sample:
        if line:
            while match_order[current].get_match_object(line) is None:
                current += 1
                if current >= len(match_order):
                    raise ValueError("Incorrect xmage save file")
    return midlines


def sniff_plain(sample: Sequence) -> Callable[[str], Optional[CardCountSecTy]]:
    h = HandleTextline()
    for line in sample:
        if not h.sniff(line):
            raise ValueError("Incorrect plain text format")
    return h


def sniff_reader(file: _io._TextIOBase, num: int=40) \
        -> Callable[[io.IOBase], Tuple[CardListTy, CardListTy]]:
    pos = file.tell()
    header = file.readline()
    sample = header + "".join(itertools.islice(file, num - 1))  # read first N lines to sniff
    ret = None
    try:
        dialect = csv.Sniffer().sniff(sample, (";", ","))
    except csv.Error:
        try:
            linereader = sniff_xmage(sample.splitlines())
        except ValueError:
                linereader = sniff_plain(sample.splitlines())
                print("Plain text guessed")
                ret = lambda line: read_txt(line, line_reader=linereader)
        else:
            print("Xmage save file guessed")
            ret = lambda line: read_xmage_deck(line, line_reader=linereader)
    else:
        print("CSV input guessed")
        v = csv.reader([header], dialect=dialect)
        line = list(map(str.lower, next(v)))
        count_column = line.index("count")
        name_column = line.index("name")
        try:
            section_column = line.index("section")
        except ValueError:
            section_column = None
        try:
            version_column = line.index("edition")
        except ValueError:
            version_column = None
        ret = lambda file: read_csv(file,
                                    name_column=name_column,
                                    count_column=count_column,
                                    version_column=version_column,
                                    section_column=section_column,
                                    dialect=dialect)
    file.seek(pos)
    return ret

def read_any_file(file: _io._TextIOBase) \
        -> Tuple[CardListTy, CardListTy]:
    reader = sniff_reader(file)
    return reader(file)
