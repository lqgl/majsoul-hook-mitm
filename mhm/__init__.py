from rich.console import Console
from rich.logging import RichHandler
from dataclasses import dataclass, asdict, field
from os.path import exists
from os import environ
from json import load, dump
from logging import getLogger
from pathlib import Path

ROOT = Path(".")

CONF_PATH = ROOT / "mhmp.json"
RESVER_PATH = ROOT / "resver.json"


@dataclass
class ResVer:
    version: str = None
    max_charid: int = None
    emos: dict[str, list] = None


@dataclass
class Conf:
    @dataclass
    class Base:
        log_level: str = "info"
        pure_python_protobuf: bool = False

    @dataclass
    class Plugin:
        enable_skins: bool = True
        enable_aider: bool = False
        enable_chest: bool = False
        random_star_char: bool = False

    mhm: Base = field(
        default_factory=lambda: Conf.Base(),
    )
    plugin: Plugin = field(
        default_factory=lambda: Conf.Plugin(),
    )
    dump: dict = field(
        default_factory=lambda: {
            "with_dumper": False,
            "with_termlog": True,
        }
    )
    mitmdump: dict = field(
        default_factory=lambda: {
            "http2": False,
            "mode": ["socks5@127.0.0.1:7070"],
        }
    )
    proxinject: dict = field(
        default_factory=lambda: {
            "name": "jantama_mahjongsoul",
            "set-proxy": "127.0.0.1:7070",
        }
    )

    @classmethod
    def fromdict(cls, data: dict):
        # purge
        if (tmp := "server") in data:
            del data[tmp]
        # to dataclass
        for key, struct in [("mhm", cls.Base), ("plugin", cls.Plugin)]:
            if key in data:
                data[key] = struct(**data[key])
        return cls(**data)


if exists(CONF_PATH):
    conf = Conf.fromdict(load(open(CONF_PATH, "r")))
else:
    conf = Conf()

if exists(RESVER_PATH):
    resver = ResVer(**load(open(RESVER_PATH, "r")))
else:
    resver = ResVer()


def fetch_resver():
    """Fetch the latest character id and emojis"""
    import requests
    import random
    import re

    rand_a: int = random.randint(0, int(1e9))
    rand_b: int = random.randint(0, int(1e9))

    ver_url = f"https://game.maj-soul.com/1/version.json?randv={rand_a}{rand_b}"
    response = requests.get(ver_url, proxies={"https": None})
    response.raise_for_status()
    version: str = response.json().get("version")

    if resver.version == version:
        return

    res_url = f"https://game.maj-soul.com/1/resversion{version}.json"
    response = requests.get(res_url, proxies={"https": None})
    response.raise_for_status()
    res_data: dict = response.json()

    emos: dict[str, list] = {}
    pattern = rf"en\/extendRes\/emo\/e(\d+)\/(\d+)\.png"

    for text in res_data.get("res"):
        matches = re.search(pattern, text)

        if matches:
            charid = matches.group(1)
            emo = int(matches.group(2))

            if emo == 13:
                continue
            if charid not in emos:
                emos[charid] = []
            emos[charid].append(emo)
    for value in emos.values():
        value.sort()

    resver.version = version
    resver.max_charid = 200001 + len(emos)
    resver.emos = {key: value[9:] for key, value in sorted(emos.items())}

    with open(RESVER_PATH, "w") as f:
        dump(asdict(resver), f)


def init():
    with console.status("[magenta]Fetch the latest server version") as status:
        fetch_resver()
    if conf.mhm.pure_python_protobuf:
        environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

    with open(CONF_PATH, "w") as f:
        dump(asdict(conf), f, indent=2)


# console
console = Console()


# logger
logger = getLogger(__name__)
logger.propagate = False
logger.setLevel(conf.mhm.log_level.upper())
logger.addHandler(RichHandler(markup=True, rich_tracebacks=True))
