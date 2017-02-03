import os
from collections import Counter, defaultdict
from typing import Dict, Optional, Tuple, List, Any, Sequence, Iterable

import load_file
import output
from card import Card

CardCountTy = Tuple[Card, int]
CardDictTy = Dict[Card, int]
CardListTy = List[CardCountTy]


class Deck:
    def __init__(self, mainboard: Optional[CardDictTy] = None,
                 sideboard: Optional[CardDictTy] = None,
                 name: str = ""):
        self.name = name
        if mainboard is None:
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
    def mainboard(self) -> Counter:
        return self._mainboard

    @property
    def sideboard(self) -> Counter:
        return self._sideboard

    @property
    def full_deck(self) -> Counter:
        return self._mainboard + self._sideboard

    def remove_version_main(self) -> Counter:
        return self._remove_version(self.mainboard)

    def remove_version_side(self) -> Counter:
        return self._remove_version(self.sideboard)

    def remove_version(self) -> Tuple[Counter, Counter]:
        return self.remove_version_main(), self.remove_version_side()

    @staticmethod
    def _remove_version(count: Counter) -> Counter:
        d = Counter()
        for i, v in count.items():
            d[Card(i.name)] += v
        return d

    def __str__(self):
        def create_liststring(l: CardDictTy) -> str:
            return '\n    '.join(
                str(n) + ' ' + str(card)
                for card, n in sorted(l.items(),
                                      key=lambda x: (x[0].name, x[0].version))
            )

        ret = []
        s = 'Main deck ({0})\n    {1}'.format(str(self.number_cards_main()), create_liststring(self.mainboard))
        ret.append(s)
        if len(self.sideboard) > 0:
            d = 'Side board ({0})\n    {1}'.format(str(self.number_cards_side()), create_liststring(self.sideboard))
            ret.append(d)
        return '\n\n'.join(ret)

    def load(self, source, reader):
        def create_counter(l: Sequence[CardCountTy]) -> Counter:
            return Counter({item[0]: item[1] for item in l})

        main, side = reader(source)
        self._mainboard = create_counter(main)
        self._sideboard = create_counter(side)

    def load_deckbox_csv(self, fname: str):
        reader = load_file.read_csv
        print('Loading deck ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        print("done!")

    def load_deckbox_inventory(self, fname: str):
        def reader(source):
            return load_file.read_inventory_deckbox_org(source), []

        print('Loading inventory ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        print("done!")

    def load_txt(self, fname: str):
        reader = load_file.read_txt
        print('Loading deck ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        print("done!")

    def load_xmage(self, fname: str):
        reader = load_file.read_xmage_deck
        print('Loading deck ({0})...'.format(fname))
        with open(fname) as file:
            self.load(file, reader)
        print("done!")

    def remove_card(self, card: Card, num: Optional[int] = None) -> int:
        onum = self.remove_card_mainboard(card, num)
        if num is None or onum < num:
            onum += self.remove_card_sideboard(card, num)
        return onum

    def remove_card_mainboard(self, card: Card, num: Optional[int] = None) -> int:
        return self._remove_card_board(self._mainboard, card, num)

    def remove_card_sideboard(self, card: Card, num: Optional[int] = None) -> int:
        return self._remove_card_board(self._sideboard, card, num)

    @staticmethod
    def _remove_card_board(test_seq, card: Card, num: Optional[int] = None) -> int:
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

    def output_deck(self, target, writer, *args, **kwargs) -> None:
        writer(self, target, *args, **kwargs)

    def output_latex_proxies(self, fname: str, image_files: Dict[Card, str], image_directory: str = "",
                             template_name: str = "template.tex", **kwargs):
        writer = output.OutputLatex(image_directory, **kwargs)
        image_list = {image_files[c]: n for c, n in self.full_deck.items()}
        writer.load_image_list(image_list)

        def writer_encapsulation(dck: "deck", target, *args, **kwargs):
            return writer(target, template_name, *args, **kwargs)

        with open(fname, "w") as f:
            self.output_deck(f, writer=writer_encapsulation)

    def __add__(self, other: "Deck") -> "Deck":
        return Deck(self.mainboard + other.mainboard, self.sideboard + other.sideboard)

    def __iadd__(self, other: "Deck") -> "Deck":
        self._mainboard += other.mainboard
        self._sideboard += other.sideboard
        return self

    def __radd__(self, other: "Deck") -> "Deck":
        if other == 0:
            return self
        else:
            return other + self

    def contains_variant(self, item):
        return any(item.alike(other) for other in self.full_deck)

    def __contains__(self, item):
        return item in self.mainboard or item in self.sideboard

    def find_all_copies(self, item: Card, area: Optional[CardDictTy] = None) \
            -> CardListTy:
        if area is None:
            area = self.full_deck
        return [(c, n) for c, n in area.items() if item.alike(c)]


def remove_basic_lands(dck: Deck, basics: Optional[Iterable[Card]] = None):
    if basics is None:
        lands = [Card("plains"), Card("island"), Card("swamp"), Card("mountain"), Card("forest")]
    else:
        lands = basics
    for i in dck.mainboard:
        if any(i.name == j.name for j in lands):
            dck.mainboard[i] = 0


def exclude_inventory(dck: Deck, inventory: Deck) -> Deck:
    if inventory is None:
        inv_counter = Counter()
    else:
        inv_counter = inventory.full_deck
    main_out = Counter()
    side_out = Counter()
    outskipped = Counter()

    view = sorted(dck.full_deck.items(), key=lambda x: (x[0].name, x[0].version), reverse=True)
    for card, num in view:
        if num > 0:
            num_owned = sum(num for item, num in inv_counter.items() if card.alike(item))
            num_skipped = sum(num for item, num in outskipped.items() if card.alike(item))
            if num_skipped < num_owned:
                onum = num
                num -= min(num_owned - num_skipped, num)
                outskipped[card] = min(num_owned, num_skipped + num)
                print("skipped {0} {1}".format(onum - num, card))
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
    print(mydeck)
