import pytest
import card


@pytest.mark.parametrize("card_left, card_right, expected", [
    (card.Card("test", edition="a", language="b"), card.Card("test", edition="a", language="b"), True),
    (card.Card("test", edition="a", language="b"), card.Card("test", edition="a"), True),
    (card.Card("test", edition="a"), card.Card("test", edition="a", language="b"), True),
    (card.Card("test", edition="a"), card.Card("test", edition="a"), True),
    (card.Card("test", edition="a", language="b"), card.Card("test", language="b"), True),
    (card.Card("test", language="b"), card.Card("test", edition="a", language="b"), True),
    (card.Card("test", language="b"), card.Card("test",language="b"), True),
    (card.Card("test"), card.Card("test"), True),

    (card.Card("test", edition="a", language="c"), card.Card("test", edition="a", language="b"), False),
    (card.Card("test", edition="c"), card.Card("test", edition="a", language="b"), False),
    (card.Card("c", edition="a", language="b"), card.Card("test"), False),
])
def test_alike(card_left, card_right, expected):
    assert card_left.alike(card_right) == expected


@pytest.mark.parametrize("card_left, card_right, expected", [
    (card.Card("test", edition="a", language="b"), card.Card("test", edition="a", language="b"), True),
    (card.Card("test", edition="a", language="b"), card.Card("test", edition="a"), True),
    (card.Card("test", edition="a"), card.Card("test", edition="a", language="b"), False),
    (card.Card("test", edition="a"), card.Card("test", edition="a"), True),
    (card.Card("test", edition="a", language="b"), card.Card("test", language="b"), True),
    (card.Card("test", language="b"), card.Card("test", edition="a", language="b"), False),
    (card.Card("test", language="b"), card.Card("test",language="b"), True),
    (card.Card("test"), card.Card("test"), True),

    (card.Card("test", edition="a", language="c"), card.Card("test", edition="a", language="b"), False),
    (card.Card("test", edition="c"), card.Card("test", edition="a", language="b"), False),
    (card.Card("c", edition="a", language="b"), card.Card("test"), False),
])
def test_is_specific(card_left, card_right, expected):
    assert card_left.is_specific(card_right) == expected
