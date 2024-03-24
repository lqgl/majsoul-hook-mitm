import json
import random
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path

import requests

from .resource import ResourceManager

HOST = "https://game.maj-soul.com/1"
ROOT = Path(".")

CONFIG_PATH = ROOT / "mhmp.json"

LQBIN_RKEY = "res/config/lqc.lqbin"
LQBIN_VTXT = ROOT / "lqc.txt"
LQBIN_PATH = ROOT / "lqc.lqbin"


@dataclass
class Config:
    @dataclass
    class Base:
        skins: bool = True
        aider: bool = False
        chest: bool = False
        debug: bool = False
        random_star_char: bool = False
        no_cheering_emotes: bool = True

    @dataclass
    class Mitmdump:
        dump: dict = field(
            default_factory=lambda: {"with_dumper": False, "with_termlog": True}
        )
        args: dict = field(
            default_factory=lambda: {"http2": False, "listen_host": "127.0.0.1", "listen_port": 7878, "mode": ["regular"]}
        )

    @dataclass
    class Proxinject:
        enable: bool = False
        path: str = str(Path("./proxinject/proxinjector-cli"))
        args: dict = field(
            default_factory=lambda: {
                "name": "jantama_mahjongsoul",
                "set-proxy": "127.0.0.1:7878",
            }
        )
    
    @dataclass
    class Playwright:
        enable: bool = True
        args: dict = field(
            default_factory=lambda: {
                "width": 1280,
                "height": 720,
                "moqiedelay": True
            }
        )
        auto_next_args: dict = field(
            default_factory=lambda: {
                "next_game_Rank": "gold",
                "next_game_number": "4p",
                "next_game_rounds": "south"
            }
        )
        auto_emotion: bool = False
        
    base: Base = field(default_factory=lambda: Config.Base())
    mitmdump: Mitmdump = field(default_factory=lambda: Config.Mitmdump())
    proxinject: Proxinject = field(default_factory=lambda: Config.Proxinject())
    playwright: Playwright = field(default_factory=lambda: Config.Playwright())

    @classmethod
    def fromdict(cls, data: dict):
        try:
            for field in fields(cls):
                if is_dataclass(field.type) and field.name in data:
                    data[field.name] = field.type(**data[field.name])
            return cls(**data)
        except (TypeError, KeyError):
            print("Configuration file is outdated, please delete it manually")
            raise


def load_resource() -> tuple[str, ResourceManager]:
    rand_a: int = random.randint(0, int(1e9))
    rand_b: int = random.randint(0, int(1e9))

    ver_url = f"{HOST}/version.json?randv={rand_a}{rand_b}"
    response = requests.get(ver_url, proxies={"https": None})
    response.raise_for_status()
    version: str = response.json()["version"]

    res_url = f"{HOST}/resversion{version}.json"
    response = requests.get(res_url, proxies={"https": None})
    response.raise_for_status()
    lqbin_version: dict = response.json()["res"][LQBIN_RKEY]["prefix"]

    # Using Cache
    if LQBIN_VTXT.exists():
        with LQBIN_VTXT.open("r") as txt:
            if txt.read() == lqbin_version:
                with LQBIN_PATH.open("rb") as qbin:
                    return lqbin_version, ResourceManager(
                        qbin.read(), config.base.no_cheering_emotes
                    ).build()

    qbin_url = f"{HOST}/{lqbin_version}/{LQBIN_RKEY}"
    response = requests.get(qbin_url, proxies={"https": None})
    response.raise_for_status()

    with LQBIN_PATH.open("wb") as qbin:
        qbin.write(response.content)
    with LQBIN_VTXT.open("w") as txt:
        txt.write(lqbin_version)
    return lqbin_version, ResourceManager(
        response.content, config.base.no_cheering_emotes
    ).build()


if CONFIG_PATH.exists():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = Config.fromdict(json.load(f))
else:
    config = Config()
with CONFIG_PATH.open("w", encoding="utf-8") as f:
    json.dump(asdict(config), f, indent=2, ensure_ascii=False)