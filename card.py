class Card:
    __slots__ = ["_version", "_name"]

    def __init__(self, name: str, version: str = ""):
        self._name = name
        self._version = version

    def alike(self, other: "Card") -> bool:
        sv = MTGSET_CODES.get(self.version, self.version)
        ov = MTGSET_CODES.get(other.version, other.version)
        return self.name == other.name and (not sv or sv == ov)

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.name == other.name and self.version == other.version

    def __hash__(self):
        return hash((self.name, self.version))

    def __str__(self):
        if self.version == "":
            return self.name
        else:
            return self.name + " [" + self.version + "]"

    def __repr__(self):
        return type(self).__name__ + "(name=" + repr(self.name) + ", " + "version=" + repr(self.version) + ")"


# start
MTGSET_CODES = {
    "limit edition alpha": "lea",
    "limit edition beta": "leb",
    "unlimited edition": "2ed",
    "revised edition": "3ed",
    "fourth edition": "4ed",
    "fifth edition": "5ed",
    "classic sixth edition": "6ed",
    "seventh edition": "7ed",
    "eighth edition": "8ed",
    "ninth edition": "9ed",
    "tenth edition": "10e",
    "magic 2010": "m10",
    "magic 2011": "m11",
    "magic 2012": "m12",
    "magic 2013 core set": "m13",
    "magic 2014 core set": "m14",
    "magic origins": "ori",

    "arabian nights": "arn",
    "antiquities": "atq",
    "legends": "leg",
    "the dark": "drk",
    "fallen empires": "fem",
    "homelands": "hml",
    "ice age": "ice",
    "alliances": "all",
    "coldsnap": "csp",
    "mirage": "mir",
    "visions": "vis",
    "weatherlight": "wth",
    "tempest": "tmp",
    "stronghold": "sth",
    "exodus": "exo",
    "urza's sage": "usg",
    "urza's legacy": "ulg",
    "urza's destiny": "uds",
    "mercadian masques": "mmq",
    "nemesis": "nem",
    "prophecy": "pcy",
    "invasion": "inv",
    "planeshift": "pls",
    "apocalypse": "apc",
    "odyssey": "ody",
    "torment": "tor",
    "judgement": "jud",
    "onslaught": "ons",
    "legions": "lgn",
    "scourge": "scg",
    "mirrodin": "mrd",
    "darksteel": "dst",
    "fifth dawn": "5dn",
    "champions of kamigawa": "chk",
    "betrayers of kamigawa": "bok",
    "saviors of kamigawa": "sok",
    "ravnica: city of guilds": "rav",
    "guildpact": "gpt",
    "dissension": "dis",
    "time spiral": "tsp",
    "planar chaos": "plc",
    "future sight": "fut",
    "lorwyn": "lrw",
    "morningtide": "mor",
    "shadowmoor": "shm",
    "eventide": "eve",
    "shards of alara": "ala",
    "conflux": "con",
    "alara reborn": "arb",
    "zendikar": "zen",
    "worldwake": "wwk",
    "rise of the eldrazi": "roe",
    "scars of mirrodin": "som",
    "mirrodin besieged": "mbs",
    "new phyrexia": "nph",
    "innistrad": "isd",
    "dark scension": "dka",
    "avacyn restored": "avr",
    "return to ravnica": "rtr",
    "gatecrash": "gtc",
    "dragon's maze": "dgm",
    "theros": "ths",
    "born of the gods": "bng",
    "journey into nyx": "jou",
    "khans of tarkir": "ktk",
    "fater reforged": "frf",
    "dragons of tarkir": "dtk",
    "battle for zendikar": "bfz",
    "oath of the gatewatch": "ogw",
    "shadows over innistrad": "soi",
    "eldritch moon": "emn",
    "kaladesh": "kld",
    "aether revolt": "aer",
    "amonkhet": "akh",
    "hour of devastation": "hou",

    "chronicles": "chr",
    "anthologies": "ath",
    "battle royale box set": "brb",
    "beatdown box set": "btd",
    "deckmasters: garfield vs. finkel": "dkm",
    "eternal masters": "ema",
    "duel decks: elves vs. goblins": "evg",
    "duel decks: jace vs. chandra": "dd2",
    "duel decks: divine vs. demonic": "ddc",
    "duel decks: garruk vs. liliana": "ddd",
    "duel decks: phyrexia vs. the coalition": "dde",
    "duel decks: elspeth vs. tezzeret": "ddf",
    "duel decks: knights vs. dragons": "ddg",
    "duel decks: ajani vs. nicol bolas": "ddh",
    "duel decks: venser vs. koth": "ddi",
    "duel decks: izzet vs. golgari": "ddj",
    "duel decks: sorin vs. tibalt": "ddk",
    "duel decks: heroes vs. monsters": "ddl",
    "duel decks: jace vs. vraska": "ddm",
    "duel decks: speed vs. cunning": "ddn",
    "duel decks anthology": "dd3",
    "duel decks: elspeth vs. kiora": "ddo",
    "duel decks: zendikar vs. eldrazi": "ddp",
    "duel decks: blessed vs. cursed": "ddq",
    "duel decks: nissa vs. ob nixilis": "ddr",
    "duel decks: mind vs might": "dds",
    "from the vault: dragons": "drb",
    "from the vault: exiled": "v09",
    "from the vault: relics": "v10",
    "from the vault: legends": "v11",
    "from the vault: realms": "v12",
    "from the vault: twenty": "v13",
    "from the vault: annihilation": "v14",
    "from the vault: angels": "v15",
    "from the vault: lore": "v16",
    "premium deck series: slivers": "h09",
    "premium deck series: fire and lightning": "pd2",
    "premium deck series: graveborn": "pd3",
    "modern masters": "mma",
    "modern masters 2015 edition": "mm2",
    "modern masters 2017 edition": "mm3",
    "modern event deck 2014": "md1",

    "planechase": "hop",
    "planechase 2012 edition": "pc2",
    "planechase anthology": "pca",
    "archenemy": "arc",
    "commander": "cmd",
    "commander's arsenal": "cma",
    "commander 2013 edition": "c13",
    "commander 2014": "c14",
    "commander 2015": "c15",
    "commander 2016": "c16",
    "commander anthology": "cma",
    "conspiracy": "cns",
    "conspiracy: take the crown": "cn2",

    "portal": "por",
    "portal second age": "po2",
    "portal three kingdoms": "ptk",
    "starter 1999": "s99",
    "starter 2000": "s00",

    "collector's edition": "ced",
    "international collector's edition": "ced",
    "unglued": "ugl",
    "unhinged": "unh"
}

# synonyms
__append = {
    "alpha": "lea",
    "beta": "leb",
    "sixth edition": "6ed",
    "magic 2013": "m13",
    "magic 2014": "m14",
    "ravnica": "rav",
    "third edition": "3ed",
    "3rd edition": "3ed",
    "4th edition": "4ed",
    "5th edition": "5ed",
    "6th edition": "6ed",
    "7th edition": "7ed",
    "8th edition": "8ed",
    "9th edition": "9ed",
    "10th edition": "10e",
    "origins": "ori"
}
MTGSET_CODES = {n.lower(): v.lower() for n, v in MTGSET_CODES.items()}
MTGSET_CODES.update(__append)
__append = {}
for name, short in MTGSET_CODES.items():
    t = " edition"
    if name.endswith(t) and len(name) > len(t):
        __append[name[:-len(t)]] = short
MTGSET_CODES.update(__append)
__append = {}
for name, short in MTGSET_CODES.items():
    dd = "duel decks: "
    ftv = "from the vault: "
    if name.startswith(dd) and len(name) > len(dd):
        __append[name[len(dd):]] = short
    elif name.startswith(ftv) and len(name) > len(ftv):
        __append["ftv: " + name[len(ftv):]] = short
MTGSET_CODES.update(__append)

MTGSET_CODES = {n.lower(): v.lower() for n, v in MTGSET_CODES.items()}
