import copy
import os
import itertools
from collections import Counter
from typing import Dict, Tuple, Sequence, Union, TextIO
from typing import Iterable, Callable, Any, Mapping, AnyStr

import load_file
import save_file
from card import Card
from proxy import output

import mylogger
from proxybuilder_types import CardCountTy, CardDictTy, CardListTy, ReadFuncTy, SaveFuncTy
from export.jsonencoders import JSONable

logger = mylogger.MAINLOGGER


class Deck(JSONable):
    def to_json(self):
        d = super().to_json()
        l = list(self._mainboard.items())
        d["mainboard"] = l
        l = list(self._sideboard.items())
        d["sideboard"] = l
        d.update({"name": self.name})
        return d

    @classmethod
    def from_json(cls, mainboard, sideboard, **kwargs):
        return cls(mainboard=dict(mainboard), sideboard=dict(sideboard), **kwargs)

    def __init__(self, mainboard: Union[Sequence[Card], Mapping[Card, int]] = None,
                 sideboard: Union[Sequence[Card], Mapping[Card, int]] = None,
                 name: AnyStr = ""):
        self.name = name
        if mainboard is None or len(mainboard) == 0:
            self._mainboard = Counter()
        else:
            self._mainboard = Counter(mainboard)

        if sideboard is None:
            self._sideboard = Counter()
        else:
            self._sideboard = Counter(sideboard)

    def add_main(self, card: Card, num: int = 1):
        self._mainboard[card] += num

    def add_side(self, card: Card, num: int = 1):
        self._sideboard[card] += num

    def number_cards_main(self) -> int:
        return sum(self.mainboard.values())

    def number_cards_side(self) -> int:
        return sum(self.sideboard.values())

    @property
    def mainboard(self) -> CardDictTy:
        return self._mainboard

    @property
    def sideboard(self) -> CardDictTy:
        return self._sideboard

    @property
    def full_deck(self) -> CardDictTy:
        return self._mainboard + self._sideboard

    def remove_version_main(self) -> CardDictTy:
        return self._remove_version(self.mainboard)

    def remove_version_side(self) -> CardDictTy:
        return self._remove_version(self.sideboard)

    def remove_version(self) -> Tuple[CardDictTy, CardDictTy]:
        return self.remove_version_main(), self.remove_version_side()

    @staticmethod
    def _remove_version(count: CardDictTy) -> CardDictTy:
        d = Counter()
        for i, v in count.items():
            d[Card(i.name)] += v
        return d

    def __str__(self):
        def create_liststring(l: CardDictTy) -> str:
            return '\n    '.join(
                str(n) + ' ' + str(card)
                for card, n in sorted(l.items(),
                                      key=lambda x: (x[0].name, x[0].edition))
            )

        ret = []
        s = 'Main deck ({0})\n    {1}'.format(self.number_cards_main(),
                                              create_liststring(self.mainboard))
        ret.append(s)
        if len(self.sideboard) > 0:
            d = 'Side board ({0})\n    {1}'.format(self.number_cards_side(),
                                                   create_liststring(self.sideboard))
            ret.append(d)
        return '\n'.join(ret)

    def guarded_load(self, fname: AnyStr, readfunc: ReadFuncTy):
        print('Loading deck ({0})...'.format(fname))
        try:
            with open(fname) as f:
                self.load(f, readfunc)
        except ValueError as e:
            logger.error("While handling file {1} "
                         "the following errors occured:\n - {0};".format('\n - '.join(e.args),
                                                                         os.path.abspath(fname)))
        except (FileNotFoundError, IsADirectoryError):
            logger.error("file {0} does not exist".format(os.path.abspath(fname)))
        except PermissionError:
            logger.error("No permission to open {0}".format(os.path.abspath(fname)))
        except OSError:
            logger.error("General failure to open {0}".format(os.path.abspath(fname)))
        except BaseException:
            raise
        else:
            logger.info("Loading deck, done!")

    def load(self, source: TextIO, reader: load_file.ReadFuncTy):
        def create_counter(l: Sequence[CardCountTy]) -> Counter:
            c = Counter()
            for item in l:
                c[item[0]] += item[1]
            return c

        main, side = reader(source)
        self._mainboard = create_counter(main)
        self._sideboard = create_counter(side)

    def load_deckbox_csv(self, fname: AnyStr):
        reader = load_file.read_csv
        logger.info('Loading deck ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        logger.info("done!")

    def load_deckbox_inventory(self, fname: AnyStr):
        def reader(source):
            return load_file.read_inventory_deckbox_org(source), []

        logger.info('Loading inventory ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        logger.info("done!")

    def load_txt(self, fname: AnyStr):
        reader = load_file.read_txt
        logger.info('Loading deck ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        logger.info("done!")

    def load_xmage(self, fname: AnyStr):
        reader = load_file.read_xmage_deck
        logger.info('Loading deck ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        logger.info("done!")

    def guarded_save(self, fname: AnyStr, exportfunc: SaveFuncTy):
        print('Exporting deck ({0})...'.format(fname))
        try:
            with open(fname, 'w') as f:
                self.save(f, exportfunc)
        except ValueError as e:
            logger.error("While handling file {1} "
                         "the following errors occured:\n - {0};".format('\n - '.join(e.args),
                                                                         os.path.abspath(fname)))
        except (FileNotFoundError, IsADirectoryError):
            logger.error("file {0} does not exist".format(os.path.abspath(fname)))
        except PermissionError:
            logger.error("No permission to open {0}".format(os.path.abspath(fname)))
        except OSError:
            logger.error("General failure to open {0}".format(os.path.abspath(fname)))
        except BaseException:
            raise
        else:
            logger.info("Exporting deck, done!")

    def save(self, outstream: TextIO, saver):
        saver(outstream, self.mainboard.items(), self.sideboard.items())

    def save_txt(self, fname: AnyStr):
        saver = save_file.save_txt
        logger.info('Saving deck ({0})...'.format(fname))
        with open(fname, 'w') as f:
            self.save(f, saver)

    def remove_card(self, card: Card, num: int = None) -> int:
        onum = self.remove_card_mainboard(card, num)
        if num is None or onum < num:
            onum += self.remove_card_sideboard(card, num)
        return onum

    def remove_card_mainboard(self, card: Card, num: int = None) -> int:
        return self._remove_card_board(self._mainboard, card, num)

    def remove_card_sideboard(self, card: Card, num: int = None) -> int:
        return self._remove_card_board(self._sideboard, card, num)

    @staticmethod
    def _remove_card_board(test_seq, card: Card, num: int = None) -> int:
        onum = 0
        for look_card in test_seq:
            if card.alike(look_card):
                n = test_seq[look_card]
                if num is None or n <= (num - onum):
                    onum += n
                    test_seq[look_card] = 0
                else:
                    test_seq[look_card] -= (num - onum)
                    onum = num
        test_seq += Counter()
        return onum

    def output_deck(self, target: TextIO,
                    writer: Callable[["Deck", TextIO,
                                      Sequence[Any], Mapping[str, Any]], None],
                    *args, **kwargs) -> None:
        writer(self, target, *args, **kwargs)

    def output_latex_proxies(self, fname: str, image_files: Dict[Card, str],
                             image_directory: str = "",
                             template_name: str = "template.tex", **kwargs):
        writer = output.OutputLatex(image_directory, **kwargs)

        image_list = {image_files[c]: n for c, n in self.full_deck.items() if c in image_files}
        writer.load_image_list(image_list)

        def writer_encapsulation(dck: "Deck", target, *args, **kwargs) -> None:
            writer(target, template_name, *args, **kwargs)

        with open(fname, "w") as f:
            self.output_deck(f, writer=writer_encapsulation)

    def __add__(self, other: "Deck") -> "Deck":
        return Deck(self.mainboard + other.mainboard, self.sideboard + other.sideboard)

    def __iadd__(self, other: "Deck") -> "Deck":
        self._mainboard += other.mainboard
        self._sideboard += other.sideboard
        return self

    def __radd__(self, other: "Deck") -> "Deck":
        # noinspection PyTypeChecker
        if other == 0:
            return self
        else:
            return other + self

    def __eq__(self, other: "Deck") -> bool:
        return self.mainboard == other.mainboard and self.sideboard == other.sideboard

    def contains_variant(self, item: Card) -> bool:
        return any(item.alike(other)
                   for other in itertools.chain(self.mainboard, self.sideboard))

    def __contains__(self, item: Card) -> bool:
        return item in itertools.chain(self.mainboard, self.sideboard)

    def find_all_copies_by_name(self, name: AnyStr, area: CardDictTy = None) \
            -> CardListTy:
        if area is None:
            area = self.full_deck
        return [(c, n) for c, n in area.items() if c.name == name]

    def find_all_copies(self, item: Card, area: CardDictTy = None) \
            -> CardListTy:
        if area is None:
            area = self.full_deck
        return [(c, n) for c, n in area.items() if item.alike(c)]


# noinspection PyProtectedMember
def remove_basic_lands(dck: Deck, basics: Iterable[Card] = None) -> Deck:
    outdck = copy.deepcopy(dck)
    if basics is None:
        lands = [Card("plains"), Card("island"), Card("swamp"), Card("mountain"), Card("forest")]
    else:
        lands = basics
    for i in outdck.mainboard:
        if any(i.name.lower() == j.name for j in lands):
            outdck.mainboard[i] = 0
    for i in outdck.sideboard:
        if any(i.name.lower() == j.name for j in lands):
            outdck.sideboard[i] = 0
    outdck._mainboard += Counter()
    outdck._sideboard += Counter()
    return outdck


def exclude_inventory(dck: Deck, inventory: Deck) -> Deck:
    inv_counter = inventory.full_deck
    main_out = Counter()
    side_out = Counter()
    outskipped = Counter()

    view = sorted(dck.full_deck.items(), key=lambda x: (x[0].name, x[0].edition), reverse=True)
    for card, num in view:
        if num > 0:
            num_owned = sum(num for item, num in inv_counter.items() if card.alike(item))
            num_skipped = sum(num for item, num in outskipped.items() if card.alike(item))
            if num_skipped < num_owned:
                onum = num
                num -= min(num_owned - num_skipped, num)
                outskipped[card] = min(num_owned, num_skipped + num)
                logger.debug(verbose_msg="Removed {0} {1}".format(onum - num, card))
            if num > 0:
                if card in dck.mainboard:
                    main_out[card] += num
                else:
                    side_out[card] += num
    return Deck(main_out, side_out)


if __name__ == "__main__":
    PROJECTNAME = 'proxylist'
    PROJECTDIR = os.path.expanduser('~/' + PROJECTNAME + '/')

    mydeck = Deck()
    mydeck.load_deckbox_csv(os.path.join(PROJECTDIR, "input.csv"))
    logger.info(mydeck)
