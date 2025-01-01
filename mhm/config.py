import random
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
import requests
from loguru import logger

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
        force_update: bool = False  # 是否强制更新资源
        cache_version: str = ""     # 缓存的版本号

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


def update_yaml_config(config_data):
    """更新 YAML 配置文件，保留注释"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096  # 防止自动换行
    yaml.indent(mapping=2, sequence=4, offset=2)
    
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open('r', encoding='utf-8') as f:
            current_yaml = yaml.load(f)
    else:
        current_yaml = {}
        
    # 递归更新配置，保留注释
    def update_dict(current, new):
        for k, v in new.items():
            if isinstance(v, dict) and k in current:
                update_dict(current[k], v)
            elif isinstance(v, list) and k in current and isinstance(current[k], CommentedSeq):
                # 保存原有列表项的注释
                old_comments = []
                for i, item in enumerate(current[k]):
                    if hasattr(item, 'comment'):
                        old_comments.append((i, item.comment))
                
                # 更新列表
                current[k].clear()
                current[k].extend(v)
                
                # 恢复注释
                for i, comment in old_comments:
                    if i < len(current[k]):
                        current[k][i].comment = comment
            else:
                current[k] = v

    update_dict(current_yaml, config_data)
    
    with CONFIG_PATH.open('w', encoding='utf-8') as f:
        yaml.dump(current_yaml, f)

def load_resource(no_cheering_emotes: bool) -> ResourceManager:
    # 如果不强制更新且存在缓存版本号，直接尝试加载缓存
    if not config.base.force_update and config.base.cache_version and LQBIN_PATH.exists():
        try:
            with LQBIN_PATH.open("rb") as bin:
                return ResourceManager(bin.read(), config.base.cache_version, no_cheering_emotes).build()
        except Exception as e:
            logger.warning(f"Failed to load cached resource: {e}")
    
    # 获取最新版本
    rand_a: int = random.randint(0, int(1e9))
    rand_b: int = random.randint(0, int(1e9))
    
    with requests.Session() as s:
        ver_url = f"{HOST}/version.json?randv={rand_a}{rand_b}"
        response = s.get(ver_url, proxies={"https": None})
        response.raise_for_status()
        version: str = response.json()["version"]

        res_url = f"{HOST}/resversion{version}.json"
        response = s.get(res_url, proxies={"https": None}, stream=True)
        response.raise_for_status()
        bin_version: str = response.json()["res"][LQBIN_RKEY]["prefix"]

        # 如果版本相同且不强制更新，使用缓存
        if not config.base.force_update and bin_version == config.base.cache_version and LQBIN_PATH.exists():
            with LQBIN_PATH.open("rb") as bin:
                return ResourceManager(bin.read(), bin_version, no_cheering_emotes).build()

        # 下载新版本
        bin_url = f"{HOST}/{bin_version}/{LQBIN_RKEY}"
        response = s.get(bin_url, proxies={"https": None}, stream=True)
        response.raise_for_status()

        content = b"".join(response.iter_content(chunk_size=8192))
        with LQBIN_PATH.open("wb") as bin:
            bin.write(content)
        
        # 更新配置文件中的版本号
        if bin_version != config.base.cache_version:
            config.base.cache_version = bin_version
            update_yaml_config(asdict(config))

        return ResourceManager(content, bin_version, no_cheering_emotes).build()


def load_config():
    yaml = YAML()
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open('r', encoding='utf-8') as f:
            config_data = yaml.load(f)
        return Config.fromdict(config_data)
    else:
        config = Config()
        update_yaml_config(asdict(config))
        return config

config = load_config()
