import os
import argparse
from collections import Counter
from typing import Sequence, Tuple, Any, Dict, TypeVar, Optional

import deck
import card
import output
import image_downloader as imd


PROJECTNAME = 'proxylist'
PROJECTDIR = os.path.expanduser('~/' + PROJECTNAME + '/')


def setup(projectname, projectdirectory):
    if not os.path.exists(projectdirectory):
        os.makedirs(projectdirectory)
    imagedirectory = r"images/"
    if not os.path.exists(projectdirectory + imagedirectory):
        os.makedirs(projectdirectory + imagedirectory)
    return projectname, projectdirectory, imagedirectory



class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: any):
        raise AttributeError(message)


def setup_parser():
    parser = ArgumentParser(description="Process mtg decks")
    subparsers = parser.add_subparsers(help="Action to do with the deck")
    parser_proxy = subparsers.add_parser("proxy",
                                         help="create a proxy deck")
    parser.add_argument("deck",
                        help="Input deck filename")
    parser.add_argument("-i", "--inventory",
                        help="Inventory filename")
    parser.add_argument("-f", "--figures",
                        help="Proxy image folder")
    parser.add_argument("-t", "--type",
                        help="Input type")
    parser_proxy.add_argument("-p", "--paper",
                              help="Paper namer or dimensions")
    parser_proxy.add_argument("-m", "--margins",
                              nargs=2,
                              type=int,
                              metavar=("horizontal", "vertical"),
                              help="margin dimensions (mm)")
    parser_proxy.add_argument("-c", "--cutthick",
                              type=int,
                              help="cut thickness (mm)")
    parser_proxy.add_argument("--cutcol",
                              help="cut colour")
    parser_proxy.add_argument("--template",
                              default="template.tex",
                              help="template file")
    return parser


def main():
    parser = setup_parser()

    projectname, projectdirectory, imagedirectory = setup(PROJECTNAME, PROJECTDIR)

    mydeck = deck.Deck()
    mydeck.load_xmage(os.path.join(PROJECTDIR, "racing_dwarves.dck"))
    print(mydeck)

    myinventory = deck.Deck()
    myinventory.load_deckbox_inventory(os.path.join(PROJECTDIR, "inventory.csv"))
    # print(myinventory)
    c = myinventory.find_all_copies(card.Card("angel of invention"))[0][0]

    myinventory = deck.Deck(Counter(8 * [c]))

    proxies = deck.exclude_inventory(mydeck, myinventory)

    img_fnames = imd.get_all_images(proxies, os.path.join(projectdirectory, imagedirectory))

    print(proxies)

    proxies.output_latex_proxies(os.path.join(PROJECTDIR, "test.tex"), img_fnames,
                                 template="template.tex",
                                 image_directory=imagedirectory,
                                 mypaper="a4paper",
                                 cut_thickness=1,
                                 cut_color="black")
    exit()


if __name__ == "__main__":
    main()
