from rich.console import Console
from rich.logging import RichHandler
from dataclasses import dataclass, asdict
from os.path import exists
from os import environ
from json import load, dump
from logging import getLogger
from pathlib import Path

root = Path(".")


@dataclass
class Config:
    @dataclass
    class Base:
        log_level: str
        pure_python_protobuf: bool

    @dataclass
    class Server:
        version: str
        max_charid: int

    @dataclass
    class Plugin:
        enable_skins: bool
        enable_aider: bool
        enable_chest: bool
        random_star_char: bool

    mhm: Base
    server: Server
    plugin: Plugin

    dump: dict | None
    mitmdump: dict | None
    proxinject: dict | None

    def __post_init__(self):
        if isinstance(self.mhm, dict):
            self.mhm = self.Base(**self.mhm)
        if isinstance(self.server, dict):
            self.server = self.Server(**self.server)
        if isinstance(self.plugin, dict):
            self.plugin = self.Plugin(**self.plugin)


if exists(path := root / "mhmp.json"):
    with open(path, "r") as f:
        conf = Config(**load(f))
else:
    conf = Config(
        **{
            "mhm": {
                "log_level": "info",
                "pure_python_protobuf": False,
            },
            "server": {
                "version": "0.10.286.w",
                "max_charid": 200077,
            },
            "plugin": {
                "enable_skins": True,
                "enable_aider": False,
                "enable_chest": False,
                "random_star_char": False,
            },
            "dump": {
                "with_dumper": False,
                "with_termlog": True,
            },
            "mitmdump": {
                "http2": False,
                "mode": ["socks5@127.0.0.1:7070"],
            },
            "proxinject": {
                "name": "jantama_mahjongsoul",
                "set-proxy": "127.0.0.1:7070",
            },
        }
    )


def fetch_maxid():
    """Fetch the latest character id"""
    import requests
    import random

    rand_a: int = random.randint(0, int(1e9))
    rand_b: int = random.randint(0, int(1e9))

    ver_url = f"https://game.maj-soul.com/1/version.json?randv={rand_a}{rand_b}"
    response = requests.get(ver_url, proxies={"https": None})
    response.raise_for_status()
    version = response.json().get("version")

    if conf.server.version == version:
        return

    res_url = f"https://game.maj-soul.com/1/resversion{version}.json"
    response = requests.get(res_url, proxies={"https": None})
    response.raise_for_status()
    res_data = response.json()

    max_charid = 200070
    while str(f"extendRes/emo/e{max_charid}/0.png") in res_data.get("res"):
        max_charid += 1

    conf.server = conf.Server(version, max_charid)


def init():
    with console.status("[magenta]Fetch the latest server version") as status:
        fetch_maxid()
    if conf.mhm.pure_python_protobuf:
        environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

    with open(path, "w") as f:
        dump(asdict(conf), f, indent=2)


# console
console = Console()


# logger
logger = getLogger(__name__)
logger.propagate = False
logger.setLevel(conf.mhm.log_level.upper())
logger.addHandler(RichHandler(markup=True, rich_tracebacks=True))
