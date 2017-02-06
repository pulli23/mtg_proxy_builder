import os
import argparse
import re
from collections import Counter
from typing import Sequence, Tuple, Any, Dict, TypeVar, Optional

import deck
import card
import output
import paper
import load_file
import image_downloader as imd


def setup(projectname, projectdirectory):
    if not os.path.exists(projectdirectory):
        os.makedirs(projectdirectory)
    imagedirectory = r"images/"
    if not os.path.exists(projectdirectory + imagedirectory):
        os.makedirs(projectdirectory + imagedirectory)
    return projectname, projectdirectory, imagedirectory


class SetupData:
    def __init__(self, parseobj, **kwargs):
        super().__init__(**kwargs)
        for a in vars(parseobj):
            setattr(self, a, getattr(parseobj, a))

        self.input = os.path.normpath(self.input)
        self.project_directory = os.path.dirname(self.input)
        if not os.path.isabs(self.output):
            self.output = os.path.normpath(os.path.join(self.project_directory, self.output))
        if self.inventory is not None and not os.path.isabs(self.inventory):
            self.inventory = os.path.normpath(os.path.join(self.project_directory, self.inventory))
        if not os.path.isabs(self.figures):
            self.figures = os.path.normpath(os.path.join(self.project_directory, self.figures))
        all_type_reverse_keys = {load_file.read_csv: ("csv", "deckbox"),
                                 load_file.read_txt: ("txt", "text", "plain"),
                                 load_file.read_xmage_deck: ("xmage",)}
        all_type_keys = {k: fun for fun, keys in all_type_reverse_keys.items() for k in keys}
        try:
            self.readfunc = all_type_keys[self.type]
        except KeyError:
            self.readfunc = load_file.read_any_file
        if self.inventory_type is None:
            self.inventory_readfunc = self.readfunc
        else:
            try:
                self.inventory_readfunc = all_type_keys[self.inventory_type]
            except:
                self.inventory_readfunc = load_file.read_any_file
        mo = re.fullmatch(r"(\d+)x(\d+)", self.paper)
        if mo:
            self.paper = paper.Paper(width=mo[1], height=mo[2], margins=self.margins)
        else:
            self.paper = paper.Paper(name=self.paper, margins=self.margins)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: any):
        raise NameError(message)

    def parse_args(self, *args, **kwargs):
        r = super().parse_args(*args, **kwargs)
        return SetupData(r)


def setup_parser():
    parser = ArgumentParser(description="Process mtg decks")
    subparsers = parser.add_subparsers(help="Action to do with the deck")
    parser_proxy = subparsers.add_parser("proxy",
                                         help="create a proxy deck")
    parser_proxy.set_defaults(cmd="proxy")
    parser_proxy.add_argument("input",
                              help="Input deck filename")
    parser_proxy.add_argument("output",
                              help="output latex file")
    parser_proxy.add_argument("-i", "--inventory",
                        help="Inventory filename")
    parser_proxy.add_argument("-f", "--figures",
                        default="",
                        help="Proxy image folder")
    parser_proxy.add_argument("-t", "--type",
                        help="Input type")
    parser_proxy.add_argument("--inventory-type",
                        help="Inventory input type")
    parser_proxy.add_argument("-p", "--paper",
                              default='a4paper',
                              help="Paper name or dimensions")
    parser_proxy.add_argument("-m", "--margins",
                              nargs=2,
                              type=float,
                              metavar=("horizontal", "vertical"),
                              help="margin dimensions (mm)")
    parser_proxy.add_argument("-c", "--cutthick",
                              type=float,
                              default=0,
                              help="cut thickness (mm)")
    parser_proxy.add_argument("--cutcol",
                              default='black',
                              help="cut colour")
    parser_proxy.add_argument("--background",
                              help="image background colour")
    parser_proxy.add_argument("--template",
                              default="template.tex",
                              help="template file")
    parser_proxy.add_argument("--specific-edition",
                              action="store_false",
                              help="Flag to indicate card edition is important for proxies")
    parser_proxy.add_argument("--include-basics",
                              action="store_true",
                              help="Include basic lands in proxy list")
    parser_proxy.add_argument("-v","--verbose",
                              action="store_true",
                              help="Verbose printing messages")
    return parser


def main():
    PROJECTNAME = 'proxylist'
    PROJECTDIR = os.path.expanduser('~/' + PROJECTNAME + '/')
    projectname, projectdirectory, imagedirectory = setup(PROJECTNAME, PROJECTDIR)

    parser = setup_parser()
    parser.parse_args(["proxy", "-h"])
    args = parser.parse_args(
        ["proxy", os.path.expanduser("~/proxylist/racing_dwarves.dck"), "main.tex", "--specific-edition", "--cutcol", "white", "--cutthick", "0.5"])
    inv = deck.Deck()
    if args.inventory is not None:
        print('Loading inventory ({0})...'.format(args.inventory))
        with open(args.inventory) as file:
            inv.load(file, args.inventory_readfunc)
        print("done!")

    dck = deck.Deck()
    print('Loading deck ({0})...'.format(args.input))
    with open(args.input) as f:
        dck.load(f, args.readfunc)
    print("done!")

    if not args.specific_edition:
        dck = deck.Deck(*dck.remove_version())

    if not args.include_basics:
        proxies = deck.remove_basic_lands(dck)
    else:
        proxies = dck

    proxies = deck.exclude_inventory(proxies, inv)
    if args.verbose:
        print("PROXY LIST")
        print(proxies)

    image_fnames = imd.get_all_images(proxies, args.figures)
    rel_fig_dir = os.path.relpath(args.figures, os.path.dirname(args.output))
    if rel_fig_dir == ".":
        rel_fig_dir = ""
    proxies.output_latex_proxies(args.output, image_fnames, rel_fig_dir, args.template,
                                 mypaper=args.paper,
                                 cut_color=args.cutcol,
                                 cut_thickness=args.cutthick,
                                 card_dimensions=None,
                                 background_colour=args.background
                                 )


if __name__ == "__main__":
    main()
