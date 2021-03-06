import csv
import itertools
import operator
import re
import typing
from typing import Iterable, Sequence, AnyStr
from typing import Optional, Callable, Tuple

import mylogger
from card import Card
from proxybuilder_types import CardCountSecTy, CardListTy, ReadLineFuncTy, CardCountTy, ReadFuncTy
from export.jsonencoders import load_file, load_string


def read_file(file: Iterable, line_process: ReadLineFuncTy,
              *args: any, **kwargs: any) \
        -> Tuple[CardListTy, CardListTy]:
    inputlist = (line_process(row, *args, **kwargs) for row in file)
    inputlist = list(filter(None, inputlist))
    t = tuple([i[:2] for i in group]
              for key, group in itertools.groupby(inputlist, operator.itemgetter(2)))
    if len(t) < 2:
        return t[0], []
    return t[0], t[1]


def process_deckbox_deck_row(row: Tuple[AnyStr, ...]) -> Optional[CardCountSecTy]:
    try:
        return Card(row[1].lower()), int(row[0]), True if row[2].lower() == "main" else False
    except (ValueError, IndexError):
        return None


def get_language(lan_str: str):
    lookup = {
        "english": "en",
        "german": "de",
        "french": "fr",
        "italian": "it",
        "spanish": "es",
        "portugese": "pt",
        "japanese": "jp",
        "russian": "ru",
        "korean": "ko",
        "chinese": "cn",
        "traditional chinese": "tw"
    }
    return lookup.get(lan_str, lan_str)


def process_csv_row(row: Tuple[AnyStr, ...], name_column: int, count_column: int,
                    version_column: int = None, section_column: int = None,
                    collectors_num_column: int = None, language_column: int = None) \
        -> Optional[CardCountSecTy]:
    try:
        n = int(row[count_column])
        v = row[version_column].lower() if version_column is not None else None
        i = row[collectors_num_column] if collectors_num_column is not None else None
        i = int(i) if i else None
        l = get_language(row[language_column].lower()) if language_column is not None else None
        s = True if section_column is None or row[section_column].lower() == "main" else False
        c = Card(row[name_column].lower(), edition=v, collectors_number=i, language=l)
        return c, n, s
    except (ValueError, IndexError):
        return None


def process_deckbox_inventory_row(row: Tuple[AnyStr, ...]) -> Optional[CardCountTy]:
    try:
        return Card(row[2].lower(), row[3].lower()), int(row[0])
    except (ValueError, IndexError):
        return None


def read_inventory_deckbox_org(file: typing.TextIO, *args, **kwargs) \
        -> CardListTy:
    return read_csv(file, name_column=2, count_column=0,
                    section_column=None, version_column=3,
                    *args, **kwargs)[0]


def read_csv(file: typing.TextIO, name_column: int = 1, count_column: int = 0,
             section_column: int = None, version_column: int = None,
             collectors_num_column: int = None, language_column: int = None, *args, **kwargs) \
        -> Tuple[CardListTy, CardListTy]:
    csvreader = csv.reader(file, *args, **kwargs)
    return read_file(csvreader, lambda line: process_csv_row(line,
                                                             name_column,
                                                             count_column,
                                                             version_column=version_column,
                                                             section_column=section_column,
                                                             collectors_num_column=collectors_num_column,
                                                             language_column=language_column
                                                             ))


class HandleTextline:
    def __init__(self, mb_check: str = r"main(\s*(board|deck))?\s*([([{<]\d+[]>})]\s*)?:?",
                 sb_check: str = r"^side(\s*board)?\s*([([{]\d+[]})]\s*)?:?",
                 line_check: str = None):
        if line_check is None:
            version_part = r"\[[^]]+?\]"
            name_part = r"[^]0-9[\s](?:[^]0-9[]*[^]0-9[\s])?"
            line_check = r"(\d+)\s+(({0})\s+({1})|({1})\s+({0})|({0}))".format(name_part,
                                                                               version_part)
        self.prog_line = re.compile(line_check, re.IGNORECASE)
        self.prog_main = re.compile(mb_check, re.IGNORECASE)
        self.prog_side = re.compile(sb_check, re.IGNORECASE)

        self.loading_main = True

    def sniff(self, line: str) -> bool:
        line = line.strip()
        if line and re.match(self.prog_main, line) is None \
                and re.match(self.prog_side, line) is None \
                and re.fullmatch(self.prog_line, line) is None:
            return False
        else:
            return True

    def __call__(self, line: str) -> Optional[CardCountSecTy]:
        line = line.strip()
        if re.match(self.prog_main, line) is not None:
            self.loading_main = True
            return

        if re.match(self.prog_side, line) is not None:
            self.load_main = False
            return

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
            return Card(name.lower(), version.lower()), num, self.loading_main


def read_txt(file: typing.TextIO, line_reader: HandleTextline=None) \
        -> Tuple[CardListTy, CardListTy]:
    if line_reader is None:
        line_reader = HandleTextline()
    return read_file(file, line_reader)


def read_json(file: typing.TextIO) \
        -> Tuple[CardListTy, CardListTy]:
    l = load_file(file)
    return l["mainboard"], l["sideboard"]


class HandleXmageLine:
    def __init__(self, line_check: Optional[str] = None):
        if line_check is None:
            version_part = r"\[([\d\w]+):(\d+)\]"
            name_part = r"[^]0-9[\s](?:[^]0-9[]*[^]0-9[\s])?"
            line_check = r"(SB:)?\s*(\d+)\s*({1})\s\s*({0})".format(name_part, version_part)
        self.prog_line = re.compile(line_check, re.IGNORECASE)

    def get_match_object(self, line: str):
        line = line.strip().lower()
        mo = re.fullmatch(self.prog_line, line)
        return mo

    def __call__(self, line: str) -> Optional[CardCountSecTy]:
        mo = self.get_match_object(line)
        if mo is not None:
            sb = True if mo.group(1) is not None else False
            num = int(mo.group(2))
            name = mo.group(6)
            version = mo.group(4)
            colnum = mo.group(5)
            return Card(name, version, int(colnum)), num, sb
        return None


def read_xmage_deck(file: typing.TextIO, line_reader: HandleXmageLine=None) \
        -> Tuple[CardListTy, CardListTy]:
    if line_reader is None:
        line_reader = HandleXmageLine()
    return read_file(file, line_reader)


def sniff_xmage(sample: Sequence) -> Callable[[str], Optional[CardCountSecTy]]:
    midlines = HandleXmageLine()
    firstline = HandleXmageLine("name:.*")
    version_part = r"\[([\d\w]+):\d+\]"
    layout_regex = r"\(\d+,\d+\)\([\w_]+,(true|false)(,\d+)?\)\|(\(({0}(,{0})*)?\))*".format(
        version_part)
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


def sniff_json(sample: Sequence) -> bool:
    sample = str(sample)
    loaded = load_string(sample)
    return True


def sniff_reader(file: typing.TextIO, num: int = 40) -> ReadFuncTy:
    pos = file.tell()
    header = file.readline()
    sample = header + "".join(itertools.islice(file, num - 1))  # read first N lines to sniff
    ret = None
    try:
        b = sniff_json(sample)
    except ValueError:
        try:
            dialect = csv.Sniffer().sniff(sample, (";", ","))
        except csv.Error:
            try:
                linereader = sniff_xmage(sample.splitlines())
            except ValueError:
                linereader = sniff_plain(sample.splitlines())
                mylogger.MAINLOGGER.info("Plain text guessed")
                ret = lambda fp: read_txt(fp, line_reader=linereader)
            else:
                mylogger.MAINLOGGER.info("Xmage save file guessed")
                ret = lambda fp: read_xmage_deck(fp, line_reader=linereader)
        else:
            mylogger.MAINLOGGER.info("CSV input guessed")
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
            try:
                collectors_num_column = line.index("card number")
            except ValueError:
                collectors_num_column = None
            try:
                language_column = line.index("language")
            except ValueError:
                language_column = None

            ret = lambda file: read_csv(file,
                                        name_column=name_column,
                                        count_column=count_column,
                                        version_column=version_column,
                                        section_column=section_column,
                                        collectors_num_column=collectors_num_column,
                                        language_column=language_column,
                                        dialect=dialect)
    else:
        mylogger.MAINLOGGER.info("JSON file guessed")
        ret = lambda fp: read_json(fp)
    file.seek(pos)
    return ret


def read_any_file(file: typing.TextIO) \
        -> Tuple[CardListTy, CardListTy]:
    reader = sniff_reader(file)
    return reader(file)
