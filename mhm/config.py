import yaml
import random
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path

import requests

from .resource import ResourceManager

HOST = "https://game.maj-soul.com/1"
ROOT = Path(".")

CONFIG_PATH = ROOT / "mhmp.yaml"  # 修改为 YAML 文件

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
        lose_weight: bool = False
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


def load_resource(no_cheering_emotes: bool) -> ResourceManager:
    rand_a: int = random.randint(0, int(1e9))
    rand_b: int = random.randint(0, int(1e9))

    # use requests.Session() instead of open/close the connection multiple times.
    with requests.Session() as s:
        ver_url = f"{HOST}/version.json?randv={rand_a}{rand_b}"
        response = s.get(ver_url, proxies={"https": None})
        response.raise_for_status()
        version: str = response.json()["version"]

        res_url = f"{HOST}/resversion{version}.json"
        response = s.get(res_url, proxies={"https": None}, stream=True)
        response.raise_for_status()
        bin_version: str = response.json()["res"][LQBIN_RKEY]["prefix"]

        # Using Cache
        if LQBIN_VTXT.exists():
            with LQBIN_VTXT.open("r") as txt:
                if txt.read() == bin_version:
                    with LQBIN_PATH.open("rb") as bin:
                        return ResourceManager(bin.read(), bin_version, no_cheering_emotes).build()

        bin_url = f"{HOST}/{bin_version}/{LQBIN_RKEY}"
        response = s.get(bin_url, proxies={"https": None}, stream=True)
        response.raise_for_status()

        content = b"".join(response.iter_content(chunk_size=8192))
        with LQBIN_PATH.open("wb") as bin, LQBIN_VTXT.open("w") as txt:
            bin.write(content)
            txt.write(bin_version)
        return ResourceManager(content, bin_version, no_cheering_emotes).build()


if CONFIG_PATH.exists():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = Config.fromdict(yaml.safe_load(f))  # 从 YAML 文件中加载配置数据
else:
    config = Config()
