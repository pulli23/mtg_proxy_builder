Proxybuilder allows you to create proxies of decks without any effort. It is a command line tool, and creates a latex file.

Proxy images are downloader from magiccards.info: as soon as the card is added there it works.
Proxybuilder currently can read plain text (format: <number> <cardname>), (deckbox.org) csv files and xmage save files.

Simple usage, open command window/shell at script. Run:
python main.py proxy "c:\users\blah\documents\input.csv" "output.tex"

To ignore an inventory, ignore all basic lands, print on A3, minimal printing margins of 1 cm and have a gray cutting line of 0.5 mm:

python main.py proxy "c:\users\blah\documents\input.csv" "output.tex" -i "inventory.csv" -p a3paper -m 10 10 -cutthick 0.5 -cutcol darkgray


Specific help of all accepted parameters:
python main.py proxy -h