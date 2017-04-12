import re
import abc
import itertools
from collections import Counter

from typing import List, Tuple, Set, Sequence, Optional

from mylogger import MAINLOGGER
logger = MAINLOGGER


class Mana(metaclass=abc.ABCMeta):
    __metaclass__ = abc.ABCMeta
    effective_cost = 1
    separator = "/"

    def __init__(self, number):
        self.number = number

    @property
    def cmc(self):
        return self.number * type(self).effective_cost

    @property
    def name(self) -> str:
        return ' '.join(filter(None, re.split("([A-Z][^A-Z]*)", type(self).__name__)))

    @classmethod
    @abc.abstractmethod
    def can_be_paid_by(cls) -> List[Tuple["BasicTypeMana", int]]:
        return []

    @classmethod
    @abc.abstractmethod
    def mana_sign(cls) -> str:
        return ""

    def generate_mana_string(self) -> str:
        S = self.mana_sign()
        if len(S) > 1:
            S = "{{{0}}}".format(S)
        return S * self.number

    def __str__(self) -> str:
        return self.generate_mana_string()

    def __repr__(self) -> str:
        return "{0}(number={1})".format(type(self).__name__, self.number)

    @classmethod
    def get_all_subclasses(cls) -> Set[type]:
        clist = set(cls.__subclasses__())
        for c in clist:
            ret = c.get_all_subclasses()
            clist = clist.union(ret)
        return clist

    @classmethod
    def make_mana(cls, name, number) -> "Mana":
        try:
            n = int(name)
            mana = GenericMana(n * number)
        except ValueError:
            l = cls.get_all_subclasses()
            names = {class_.mana_sign(): class_ for class_ in l}
            manaclass = names[name]
            if issubclass(manaclass, Mana):
                mana = manaclass(number)
            else:
                raise ValueError("Unrecognized mana name")
        return mana


class BasicTypeMana(Mana, metaclass=abc.ABCMeta):
    @classmethod
    def can_be_paid_by(cls) -> List[Tuple["Mana", int]]:
        pay = [(cls, 1)]
        pay.extend(super().can_be_paid_by())
        return pay


class HybridMana(Mana, metaclass=abc.ABCMeta):
    separator = "/"

    @classmethod
    def can_be_paid_by(cls) -> List[Tuple["Mana", int]]:
        pay = []
        for basecls in cls.__bases__:
            if not issubclass(basecls, HybridMana):
                pay.extend(basecls.can_be_paid_by())
        return pay


class MonoColoredHybridMana(HybridMana, metaclass=abc.ABCMeta):
    effective_cost = 2

    @classmethod
    def mana_sign(cls) -> str:
        return cls.separator.join(filter(None, ("2", super().mana_sign())))

    @classmethod
    def can_be_paid_by(cls) -> List[Tuple["Mana", int]]:
        basepay = super().can_be_paid_by()
        t = [p[0] for p in basepay]
        pay = [(c, 2) for c in BasicTypeMana.__subclasses__() if c not in t]
        pay.extend(basepay)
        return pay


class PhyrexianMana(Mana, metaclass=abc.ABCMeta):
    separator = ""

    @classmethod
    def mana_sign(cls) -> str:
        return super().mana_sign() + "P"


class GenericMana(Mana):
    @classmethod
    def mana_sign(cls) -> str:
        return "X"

    @classmethod
    def can_be_paid_by(cls) -> List[Tuple[BasicTypeMana, int]]:
        pay = [(c, 1) for c in BasicTypeMana.__subclasses__()]
        pay.extend(super().can_be_paid_by())
        return pay

    def generate_mana_string(self) -> str:
        return str(self.number)


class SnowMana(Mana):
    @classmethod
    def mana_sign(cls) -> str:
        return "S"

    @classmethod
    def can_be_paid_by(cls) -> List[Tuple[BasicTypeMana, int]]:
        pay = [(c, 1) for c in BasicTypeMana.__subclasses__()]
        pay.extend(super().can_be_paid_by())
        return pay


class WhiteMana(BasicTypeMana):
    @classmethod
    def mana_sign(cls) -> str:
        return cls.separator.join(filter(None, ("W", super().mana_sign())))


class BlueMana(BasicTypeMana):
    @classmethod
    def mana_sign(cls) -> str:
        return cls.separator.join(filter(None, ("U", super().mana_sign())))


class BlackMana(BasicTypeMana):
    @classmethod
    def mana_sign(cls) -> str:
        return cls.separator.join(filter(None, ("B", super().mana_sign())))


class RedMana(BasicTypeMana):
    @classmethod
    def mana_sign(cls) -> str:
        return cls.separator.join(filter(None, ("R", super().mana_sign())))


class GreenMana(BasicTypeMana):
    @classmethod
    def mana_sign(cls) -> str:
        return cls.separator.join(filter(None, ("G", super().mana_sign())))


class ColorlessMana(BasicTypeMana):
    @classmethod
    def mana_sign(cls) -> str:
        return cls.separator.join(filter(None, ("C", super().mana_sign())))


class WhitePhyrexianMana(PhyrexianMana, WhiteMana):
    pass


class BluePhyrexianMana(PhyrexianMana, BlueMana):
    pass


class BlackPhyrexianMana(PhyrexianMana, BlackMana):
    pass


class RedPhyrexianMana(PhyrexianMana, RedMana):
    pass


class GreenPhyrexianMana(PhyrexianMana, GreenMana):
    pass


class AzoriusMana(HybridMana, BlueMana, WhiteMana):
    pass


class DimirMana(HybridMana, BlueMana, BlackMana):
    pass


class RakdosMana(HybridMana, BlackMana, RedMana):
    pass


class GruulMana(HybridMana, RedMana, GreenMana):
    pass


class SelesnyaMana(HybridMana, GreenMana, WhiteMana):
    pass


class OrzhovMana(HybridMana, WhiteMana, BlackMana):
    pass


class IzzetMana(HybridMana, BlueMana, RedMana):
    pass


class GolgariMana(HybridMana, BlackMana, GreenMana):
    pass


class BorosMana(HybridMana, RedMana, WhiteMana):
    pass


class SimicMana(HybridMana, GreenMana, BlueMana):
    pass


class HybridWhiteMana(MonoColoredHybridMana, WhiteMana):
    pass


class HybridBlueMana(MonoColoredHybridMana, BlueMana):
    pass


class HybridBlackMana(MonoColoredHybridMana, BlackMana):
    pass


class HybridRedMana(MonoColoredHybridMana, RedMana):
    pass


class HybridGreenMana(MonoColoredHybridMana, GreenMana):
    pass


def _listify_mana(mana_string) -> Sequence[str]:
    special = (s[1:-1] for s in re.findall(r"{[^}]*}", mana_string))
    mana_string = re.sub(r"{[^}]*}", "", mana_string)
    general = re.findall("\d+", mana_string)
    mana_string = re.sub("\d+", "", mana_string)
    allmana = itertools.chain(general, mana_string, special)
    return allmana


def analyse_mana_string(mana_string: str) -> Optional[List[Mana]]:
    if len(mana_string) == 0:
        return None
    cmc_list = _listify_mana(mana_string)
    tdict = Counter(cmc_list)
    t = []
    for n, c in tdict.items():
        try:
            t.append(Mana.make_mana(n, c))
        except KeyError:
            logger.error("Unknown mana: {0}".format(n))
    return t
