from rich.console import Console
from rich.logging import RichHandler
from typing import TypedDict, Optional
from os.path import exists
from os import environ
from json import load, dump
from logging import getLogger
from pathlib import Path


class _BaseDict(TypedDict):
    log_level: str
    pure_python_protobuf: bool


class _ServerDict(TypedDict):
    version: str
    max_charid: int


class _PluginDict(TypedDict):
    enable_skins: bool
    enable_aider: bool
    enable_chest: bool
    random_star_char: bool


class ConfigDict(TypedDict):
    mhm: _BaseDict
    server: _ServerDict
    plugin: _PluginDict

    dump: Optional[dict]
    mitmdump: Optional[dict]
    proxinject: Optional[dict]


root = Path(".")

conf: ConfigDict = {
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


def fetch_maxid(conf: ConfigDict):
    """Fetch the latest character id"""
    import requests
    import random

    rand_a: int = random.randint(0, int(1e9))
    rand_b: int = random.randint(0, int(1e9))

    ver_url = f"https://game.maj-soul.com/1/version.json?randv={rand_a}{rand_b}"
    response = requests.get(ver_url, proxies={"https": None})
    response.raise_for_status()
    ver_data = response.json()

    if conf["server"]["version"] == ver_data["version"]:
        return

    res_url = f"https://game.maj-soul.com/1/resversion{ver_data['version']}.json"
    response = requests.get(res_url, proxies={"https": None})
    response.raise_for_status()
    res_data = response.json()

    max_charid = 200070
    while str(f"extendRes/emo/e{max_charid}/0.png") in res_data["res"]:
        max_charid += 1

    conf["server"]: _ServerDict = {
        "version": ver_data["version"],
        "max_charid": max_charid,
    }


def init():
    global conf

    path = root / "mhmp.json"

    if exists(path):
        conf.update(load(open(path, "r")))

    with console.status("[magenta]Fetch the latest server version") as status:
        fetch_maxid(conf)
    if conf["mhm"]["pure_python_protobuf"]:
        environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

    dump(conf, open(path, "w"), indent=2)


# console
console = Console()


# logger
logger = getLogger(__name__)
logger.propagate = False
logger.setLevel(conf["mhm"]["log_level"].upper())
logger.addHandler(RichHandler(markup=True, rich_tracebacks=True))
