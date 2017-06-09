import pytest

import deck
import card


def make_test_decks():
    tests = []

    dck = deck.Deck()
    dck.add_main(card.Card("a", "1", language="1"))
    dck.add_main(card.Card("a", "2", language="2"))
    dck.add_main(card.Card("a", "2", language="1"))
    dck.add_main(card.Card("a", None, language=None))
    dck.add_main(card.Card("a", None, language="1"))
    dck.add_main(card.Card("a", "4", language=None))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"))

    def invariant(x, dck=dck, dck_left=dck_left, dck_right=dck_right):
        return card.Card("a", "1", language="1") not in x and \
               len(dck.full_deck) - len(x.full_deck) == len(dck_right.full_deck)
    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing single literal 'a,1,1'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language=None))

    def invariant(x, dck=dck, dck_left=dck_left, dck_right=dck_right):
        return card.Card("a", None, language=None) not in x

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,1,*' -> 'a,*,*'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "8", language="1"))

    def invariant(x, dck=dck, dck_left=dck_left, dck_right=dck_right):
        return card.Card("a", None, language="1") not in x and \
               len(dck.full_deck) - len(x.full_deck) == len(dck_right.full_deck)

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,8,1' -> 'a,*,1'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "20", language="20"))

    def invariant(x, dck=dck, dck_left=dck_left, dck_right=dck_right):
        return card.Card("a", None, language=None) not in x and \
               len(dck.full_deck) - len(x.full_deck) == len(dck_right.full_deck)

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,20,20' -> 'a,*,*'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "4", language="4"))

    def invariant(x, dck=dck, dck_left=dck_left, dck_right=dck_right):
        return card.Card("a", "4", language=None) not in x and \
               len(dck.full_deck) - len(x.full_deck) == len(dck_right.full_deck)

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,4,4' -> 'a,4,*'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", None, language=None))

    def invariant(x, dck=dck, dck_left=dck_left, dck_right=dck_right):
        return card.Card("a", None, language=None) not in x and \
               len(dck.full_deck) - len(x.full_deck) == len(dck_right.full_deck)

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,*,*' -> 'a,*,*'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"))
    dck_right.add_main(card.Card("a", "2", language="2"))
    dck_right.add_main(card.Card("a", "4", language="4"))
    dck_right.add_main(card.Card("a", None, language=None))
    dck_right.add_main(card.Card("a", "4", language=None))
    dck_right.add_main(card.Card("a", None, language="4"))

    def invariant(x):
        return card.Card("a", None, language="1") in x and \
               card.Card("a", "2", language="1") in x and \
               len(x.full_deck) == 2

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing lots -> left over 'a,*,1'"))

    return tests


@pytest.mark.parametrize("inv_left, inv_right, invariant",
                         make_test_decks()
                         )
def test_exclude_inventory(inv_left, inv_right, invariant):
    tested_res = deck.exclude_inventory_from_deck(inv_left, inv_right)
    assert invariant(tested_res)



def make_test_sized_decks():
    tests = []

    dck = deck.Deck()
    dck.add_main(card.Card("a", "1", language="1"), 5)

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 3)

    def invariant(x):
        return x.full_deck[card.Card("a", "1", language="1")] == 5-3
    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 3 out of 5 times literal 'a,1,1'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 6)

    def invariant(x):
        return card.Card("a", "1", language="1") not in x and \
               len(dck.full_deck) - len(x.full_deck) == len(dck_right.full_deck)

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 6 out of 5 times literal 'a,1,1'"))

    dck_left = deck.Deck()
    dck_left.add_main(card.Card("a", "1", language="1"), 2)
    dck_left.add_side(card.Card("a", "1", language="1"), 2)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 6)

    def invariant(x):
        return card.Card("a", "1", language="1") not in x and \
               len(dck.full_deck) - len(x.full_deck) == len(dck_right.full_deck)

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 6 out of 2+2 times literal 'a,1,1'"))

    dck_left = deck.Deck()
    dck_left.add_main(card.Card("a", "1", language="1"), 2)
    dck_left.add_main(card.Card("a", "1", language="2"), 2)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 6)

    def invariant(x):
        return card.Card("a", "1", language="1") not in x and x.full_deck[card.Card("a", "1", language="2")] == 2

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 6 out of 2 times literal 'a,1,1'"))

    dck_left = deck.Deck()
    dck_left.add_main(card.Card("a", "1", language="1"), 2)
    dck_left.add_main(card.Card("a", "1", language="2"), 2)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language=None), 6)

    def invariant(x):
        t = x.full_deck
        return sum(n for _, n in t.items()) == 4

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,1,*:6' from ['a,1,1':2; 'a,1,2':2]"))
    return tests


@pytest.mark.parametrize("inv_left, inv_right, invariant",
                         make_test_sized_decks()
                         )
def test_exclude_inventory_multiples(inv_left, inv_right, invariant):
    tested_res = deck.exclude_inventory_from_deck(inv_left, inv_right)
    assert invariant(tested_res)


def make_test_decks_exclude_deck():
    tests = []

    dck = deck.Deck()
    dck.add_main(card.Card("a", "1", language="1"))
    dck.add_main(card.Card("a", "2", language="2"))
    dck.add_main(card.Card("a", "2", language="1"))
    dck.add_main(card.Card("a", None, language=None))
    dck.add_main(card.Card("a", None, language="1"))
    dck.add_main(card.Card("a", "4", language=None))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"))

    def invariant(x):
        return card.Card("a", "1", language="1") not in x
    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing single literal 'a,1,1'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language=None))

    def invariant(x):
        return card.Card("a", "1", language="1") not in x

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,1,*' -> 'a,1,1'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "8", language="1"))

    def invariant(x):
        return sum(n for _, n in x.full_deck.items()) == sum(n for _, n in dck.full_deck.items())

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,8,1' -> none"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "20", language="20"))

    def invariant(x):
        return sum(n for _, n in x.full_deck.items()) == sum(n for _, n in dck.full_deck.items())

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,20,20' -> none"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "4", language="4"))

    def invariant(x):
        return sum(n for _, n in x.full_deck.items()) == sum(n for _, n in dck.full_deck.items())

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,4,4' -> none"))
    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", None, language=None))

    def invariant(x):
        return card.Card("a", None, language=None) not in x.full_deck

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,*,*' -> 'a,*,*'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"))
    dck_right.add_main(card.Card("a", "2", language="2"))
    dck_right.add_main(card.Card("a", "4", language="4"))
    dck_right.add_main(card.Card("a", None, language=None))
    dck_right.add_main(card.Card("a", "4", language=None))
    dck_right.add_main(card.Card("a", None, language="4"))

    def invariant(x):
        return card.Card("a", None, language="1") in x and \
               card.Card("a", "2", language="1") in x and \
               len(x.full_deck) == 2

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing lots -> left over 'a,*,1'"))

    return tests


@pytest.mark.parametrize("inv_left, inv_right, invariant",
                         make_test_decks_exclude_deck()
                         )
def test_exclude_deck(inv_left, inv_right, invariant):
    tested_res = deck.exclude_deck_from_inventory(inv_left, inv_right)
    assert invariant(tested_res)


def make_test_sized_decks_exclude_deck():
    tests = []

    dck = deck.Deck()
    dck.add_main(card.Card("a", "1", language="1"), 5)

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 3)

    def invariant(x):
        return x.full_deck[card.Card("a", "1", language="1")] == 5-3
    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 3 out of 5 times literal 'a,1,1'"))

    dck_left = deck.Deck(dck.full_deck)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 6)

    def invariant(x):
        return card.Card("a", "1", language="1") not in x

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 6 out of 5 times literal 'a,1,1'"))

    dck_left = deck.Deck()
    dck_left.add_main(card.Card("a", "1", language="1"), 2)
    dck_left.add_side(card.Card("a", "1", language="1"), 2)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 6)

    def invariant(x):
        return card.Card("a", "1", language="1") not in x

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 6 out of 2+2 times literal 'a,1,1'"))

    dck_left = deck.Deck()
    dck_left.add_main(card.Card("a", "1", language="1"), 2)
    dck_left.add_main(card.Card("a", "1", language="2"), 2)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language="1"), 6)

    def invariant(x):
        return card.Card("a", "1", language="1") not in x and x.full_deck[card.Card("a", "1", language="2")] == 2

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 6 out of 2 times literal 'a,1,1'"))

    dck_left = deck.Deck()
    dck_left.add_main(card.Card("a", "1", language="1"), 2)
    dck_left.add_main(card.Card("a", "1", language="2"), 2)
    dck_right = deck.Deck()
    dck_right.add_main(card.Card("a", "1", language=None), 6)

    def invariant(x):
        t = x.full_deck
        return sum(n for _, n in t.items()) == 0

    tests.append(pytest.param(dck_left, dck_right, invariant, id="removing 'a,1,*:6' from ['a,1,1':2; 'a,1,2':2]"))
    return tests


@pytest.mark.parametrize("inv_left, inv_right, invariant",
                         make_test_sized_decks_exclude_deck()
                         )
def test_exclude_deck_multiples(inv_left, inv_right, invariant):
    tested_res = deck.exclude_deck_from_inventory(inv_left, inv_right)
    assert invariant(tested_res)