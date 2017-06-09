import os
from typing import Iterable, List, AnyStr

import card
import deck
import load_file
import mylogger
import proxy.image_downloader as imd
import card_downloader as cdl

logger = mylogger.MAINLOGGER


def load_existing_decks(maindeck: deck.Deck,
                        decklist: Iterable[AnyStr],
                        readfun: load_file.ReadFuncTy,
                        other_decks: List[deck.Deck] = None) -> List[deck.Deck]:
    if other_decks is None:
        # noinspection PyShadowingNames
        other_decks = []
    for existing_deck_name in decklist:
        newdeck = deck.Deck()
        newdeck.guarded_load(existing_deck_name, readfun)
        if newdeck != maindeck and newdeck not in other_decks:
            other_decks.append(newdeck)
    return other_decks


def build_proxies(settings):
    if settings.inventory is not None:
        def inline_load(i):
            tdeck = deck.Deck()
            tdeck.guarded_load(i, settings.inventory_readfunc)
            return tdeck

        all_inv = [inline_load(i) for i in settings.inventory]
        combined_inv = sum(all_inv)
    else:
        combined_inv = deck.Deck()

    dck = deck.Deck()
    dck.guarded_load(settings.input, settings.readfunc)
    if settings.alldecks is None:
        other_decks = []
    else:
        other_decks = load_existing_decks(dck, settings.alldecks, settings.alldecks_readfunc)
    logger.info("Removing existing decks from inventory")
    for i, d in enumerate(other_decks):
        if not settings.specific_edition:
            d = deck.Deck(*d.remove_version())
        if not settings.include_basics:
            d = deck.remove_basic_lands(d)
        other_decks[i] = d
    from collections import Counter
    c = Counter()
    for other_deck in other_decks:
        c += other_deck.full_deck
    combined_other_deck = deck.Deck(c)
    combined_inv = deck.exclude_deck_from_inventory(combined_inv, combined_other_deck)

    if not settings.specific_edition:
        dck = deck.Deck(*dck.remove_version())

    if not settings.include_basics:
        proxies = deck.remove_basic_lands(dck)
    else:
        proxies = dck
    logger.info("Removing remaining inventory from input deck")

    proxies = deck.exclude_inventory_from_deck(proxies, combined_inv)

    logger.info(verbose_msg="PROXY LIST")
    logger.info(verbose_msg=str(proxies))
    session = cdl.CardDownloader()
    image_fnames = imd.get_all_images(proxies, settings.figures, session)
    rel_fig_dir = os.path.relpath(settings.figures, os.path.dirname(settings.output))
    if rel_fig_dir == ".":
        rel_fig_dir = ""
    proxies.output_latex_proxies(settings.output, image_fnames, rel_fig_dir, settings.template,
                                 mypaper=settings.paper,
                                 cut_color=settings.cutcol,
                                 cut_thickness=settings.cutthick,
                                 card_dimensions=None,
                                 background_colour=settings.background
                                 )
    tdeck = deck.exclude_inventory_from_deck(dck, proxies)
    logger.info("--- Already owned cards ---")
    logger.info(tdeck)
