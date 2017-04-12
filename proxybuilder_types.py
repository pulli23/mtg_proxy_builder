from collections import Counter
import typing
from typing import Tuple, Iterable, Sequence, Callable, Optional, Mapping, Any, Union

from card import Card

KT = typing.TypeVar('KT')  # Key type.


class CounterTy(Counter, typing.Iterable[KT]):
    @classmethod
    def fromkeys(cls, iterable, v=None):
        super().fromkeys(iterable, v)

    def __new__(cls, *args, **kwds):
        # noinspection PyProtectedMember
        if typing._geqv(cls, CounterTy):
            raise TypeError("Type CouterTy cannot be instantiated; "
                            "use counter() instead")
        return Counter.__new__(cls, *args, **kwds)

CardCountTy = Tuple[Card, int]
CardCountSecTy = Tuple[Card, int, bool]
CardIterTy = Iterable[CardCountTy]
# CounterTy = Counter  # typing.Generic[Card]  # typing.TypeVar("CounterTy", Counter, Dict)
CardDictTy = Counter
CardListTy = Sequence[CardCountTy]
ReadLineFuncTy = Callable[[str, Optional[Sequence[Any]], Optional[Mapping[str, Any]]],
                          Optional[CardCountSecTy]]
ReadFuncTy = Callable[[typing.io.TextIO], Tuple[CardListTy, CardListTy]]

SaveFuncTy = Callable[[typing.io.TextIO, CardListTy, CardListTy], None]

