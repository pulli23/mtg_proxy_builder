import os
import argparse
import re
import sys
import logging

import deck
import card
import output
import paper
import load_file
import image_downloader as imd

import mylogger

logger = logging.getLogger("Main")


class SetupData:
    def _make_normalized_path(self, other_path: str) -> str:
        return os.path.normpath(os.path.join(self.project_directory, other_path))

    def __init__(self, parseobj, **kwargs):
        super().__init__()
        for a in vars(parseobj):
            setattr(self, a, getattr(parseobj, a))

        self.input = os.path.normpath(self.input)
        self.project_directory = os.path.dirname(self.input)
        if not os.path.isabs(self.output):
            self.output = self._make_normalized_path(self.output)
        if self.inventory is not None and not os.path.isabs(self.inventory):
            self.inventory = [self._make_normalized_path(i) for i in
                              str(self.inventory).split(";")]
        if not os.path.isabs(self.figures):
            self.figures = self._make_normalized_path(self.figures)
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
            except KeyError:
                self.inventory_readfunc = load_file.read_any_file
        mo = re.fullmatch(r"(\d+)x(\d+)", str(self.paper))
        if mo:
            self.paper = paper.Paper(width=mo[1], height=mo[2], margins=self.margins)
        else:
            self.paper = paper.Paper(name=str(self.paper), margins=self.margins)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: any):
        raise argparse.ArgumentError(message)

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
                              default="images/",
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
                              action="store_true",
                              help="Flag to indicate card edition is important for proxies")
    parser_proxy.add_argument("--include-basics",
                              action="store_true",
                              help="Include basic lands in proxy list")
    parser_proxy.add_argument("-v", "--verbose",
                              action="store_true",
                              help="Verbose printing messages")
    return parser


def safe_load(fname: str, readfunc: load_file.ReadFuncTy):

    print('Loading deck ({0})...'.format(fname))
    try:
        dck = deck.Deck()
        with open(fname) as f:
            dck.load(f, readfunc)
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
        print("done!")
        return dck


def main(a=None):
    parser = setup_parser()
    args = parser.parse_args(a)

    if args.inventory is not None:
        all_inv = [safe_load(i, args.inventory_readfunc) for i in args.inventory]
        combined_inv = sum(all_inv)
    else:
        combined_inv = deck.Deck();

    dck = safe_load(args.input, args.readfunc)

    if not args.specific_edition:
        dck = deck.Deck(*dck.remove_version())

    if not args.include_basics:
        proxies = deck.remove_basic_lands(dck)
    else:
        proxies = dck

    proxies = deck.exclude_inventory(proxies, combined_inv)
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
