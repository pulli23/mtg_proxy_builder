import argparse
import os
import re
import sys

from . import export_main

import load_file
import mylogger
import save_file
from . import proxybuild_main
from proxy import paper
from proxybuilder_types import SaveFuncTy, ReadFuncTy

logger = mylogger.MAINLOGGER


# noinspection PyAttributeOutsideInit
class SetupData:
    def _make_normalized_path(self, other_path: str) -> str:
        return os.path.normpath(os.path.join(self.project_directory, other_path))

    def _load_deck_list_directory(self, uri: str):
        self.alldecks.extend(os.path.join(uri, f) for f in os.listdir(uri)
                             if os.path.isfile(os.path.join(uri, f)))

    def _load_decklist_file(self, uri: str):
        with open(uri) as f:
            self.alldecks.extend(line.strip() for line in f if line.strip())

    def _load_decklist(self, uri: str):
        if os.path.isdir(uri):
            self._load_deck_list_directory(uri)
        elif os.path.isfile(uri):
            self._load_decklist_file(uri)

    def __init__(self, parseobj: argparse.ArgumentParser):
        super().__init__()
        for a in vars(parseobj):
            setattr(self, a, getattr(parseobj, a))
        if self.verbose:
            logger.verbose = True
        {
            "proxy": self.setup_proxy,
            "export": self.setup_export
        }.get(self.cmd)()

    @staticmethod
    def find_readfunc(input_type: str) \
            -> ReadFuncTy:
        all_type_reverse_keys = {load_file.read_csv: ("csv", "deckbox"),
                                 load_file.read_txt: ("txt", "text", "plain"),
                                 load_file.read_xmage_deck: ("xmage",)}
        all_type_keys = {k: fun for fun, keys in all_type_reverse_keys.items() for k in keys}
        try:
            return all_type_keys[input_type]
        except KeyError:
            return load_file.read_any_file

    @staticmethod
    def find_exportfunc(output_type: str, fname: str = "") \
            -> SaveFuncTy:
        all_type_reverse_keys = {save_file.save_csv: ("csv", "deckbox"),
                                 save_file.save_txt: ("txt", "text", "plain"),
                                 save_file.save_xmage: ("xmage",)}
        all_type_keys = {k: fun for fun, keys in all_type_reverse_keys.items() for k in keys}
        try:
            return all_type_keys[output_type]
        except KeyError:
            if fname:
                ext = os.path.splitext(fname)[1]
                all_type_keys = {"csv": save_file.save_csv,
                                 "txt": save_file.save_txt}
                try:
                    return all_type_keys[ext]
                except KeyError:
                    return save_file.save_txt

    def setup_proxy(self):
        self.input = os.path.normpath(self.input)
        self.project_directory = os.path.dirname(self.input)
        if not os.path.isabs(self.output):
            self.output = self._make_normalized_path(self.output)
        if self.inventory is not None and not os.path.isabs(self.inventory):
            self.inventory = [i if os.path.isabs(i) else self._make_normalized_path(i)
                              for i in self.inventory.split(";")]

        if not os.path.isabs(self.figures):
            self.figures = self._make_normalized_path(self.figures)
        if self.alldecks is not None:
            alldecks_list = [i if os.path.isabs(i) else self._make_normalized_path(i)
                             for i in self.alldecks.split(";")]
            self.alldecks = []
            for d in alldecks_list:
                self._load_decklist(d)

        self.readfunc = self.find_readfunc(self.type)
        if self.inventory_type is None:
            self.inventory_readfunc = self.readfunc
        else:
            self.inventory_readfunc = self.find_readfunc(self.inventory_type)
        if self.alldecks_type is None:
            self.alldecks_readfunc = self.readfunc
        else:
            self.alldecks_readfunc = self.find_readfunc(self.alldecks_type)

        mo = re.fullmatch(r"(\d+)x(\d+)", str(self.paper))
        if mo:
            self.paper = paper.Paper(width=mo[1], height=mo[2], margins=self.margins)
        else:
            self.paper = paper.Paper(name=str(self.paper), margins=self.margins)
        self.cmd = proxybuild_main.build_proxies

    def setup_export(self):
        self.input = os.path.normpath(self.input)
        if not os.path.isabs(self.output):
            self.output = self._make_normalized_path(self.output)
        self.readfunc = self.find_readfunc(self.intype)
        self.exportfunc = self.find_exportfunc(self.outtype, self.output)
        self.cmd = export_main.export_deck


class ArgumentParser(argparse.ArgumentParser):
    def _get_action_from_name(self, name):
        """Given a name, get the Action instance registered with this parser.
        If only it were made available in the ArgumentError object. It is
        passed as it's first arg...
        """
        container = self._actions
        if name is None:
            return None
        for action in container:
            if '/'.join(action.option_strings) == name:
                return action
            elif action.metavar == name:
                return action
            elif action.dest == name:
                return action

    def error(self, message: any):
        exc = sys.exc_info()[1]
        if exc:
            exc.argument = self._get_action_from_name(exc.argument_name)
            raise exc
        super(ArgumentParser, self).error(message)

    def parse_args(self, *args, **kwargs):
        r = super().parse_args(*args, **kwargs)
        return SetupData(r)


def setup_proxy_parser(parser_proxy: argparse.ArgumentParser):
    parser_proxy.add_argument("input",
                              help="Input deck filename")
    parser_proxy.add_argument("output",
                              help="output latex file")
    parser_proxy.add_argument("-i", "--inventory",
                              help="Inventory filename")
    parser_proxy.add_argument("--alldecks",
                              help="Either folder containing all other decks, "
                                   "or file containing list of decks")
    parser_proxy.add_argument("-f", "--figures",
                              default="images/",
                              help="Proxy image folder")
    parser_proxy.add_argument("-t", "--type",
                              help="Input type")
    parser_proxy.add_argument("--inventory-type",
                              help="Inventory input type")
    parser_proxy.add_argument("--alldecks-type",
                              help="all other decks input type")
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


def setup_export_parser(parser_export: argparse.ArgumentParser):
    parser_export.add_argument("input",
                               help="Input deck filename")
    parser_export.add_argument("output",
                               help="output deck file")
    parser_export.add_argument("--outtype",
                               help="output type")
    parser_export.add_argument("--intype",
                               help="Input type")


def setup_parser():
    parser = ArgumentParser(description="Process mtg decks")
    subparsers = parser.add_subparsers(help="Action to do with the deck")
    parser_proxy = subparsers.add_parser("proxy",
                                         help="create a proxy deck")
    parser_proxy.set_defaults(cmd="proxy")
    setup_proxy_parser(parser_proxy)
    parser_export = subparsers.add_parser("export",
                                          help="export deck as new file")
    parser_export.set_defaults(cmd="export")
    setup_export_parser(parser_export)
    parser.add_argument("-v", "--verbose",
                              action="store_true",
                              help="Verbose printing messages")
    return parser


def main(a=None):
    parser = setup_parser()
    args = parser.parse_args(a)
    args.cmd(args)


if __name__ == "__main__":
    main()
