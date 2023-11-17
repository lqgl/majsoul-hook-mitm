from os import system
from requests import post


from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from socket import socket, AF_INET, SOCK_STREAM

from mhm import root
from mhm.events import manager
from mhm.proto.liqi import Msg, MsgType


disable_warnings(InsecureRequestWarning)


@manager.register(any)
def handle(msg: Msg):
    if not msg.account or msg.type == MsgType.Req:
        return

    aider = Aider.one(msg.account)

    if msg.method == ".lq.ActionPrototype":
        if msg.data["name"] == "ActionNewRound":
            msg.data["data"]["md5"] = msg.data["data"]["sha256"][:32]
        send_msg = msg.data["data"]
    elif msg.method == ".lq.FastTest.syncGame":
        for action in msg.data["game_restore"]["actions"]:
            if action["name"] == "ActionNewRound":
                action["data"]["md5"] = action["data"]["sha256"][:32]
        send_msg = {"sync_game_actions": msg.data["game_restore"]["actions"]}
    else:
        send_msg = msg.data

    post(aider.api, json=send_msg, verify=0)


class Aider:
    port: int = 43410

    _all_: dict[int, type["Aider"]] = {}

    @classmethod
    def one(cls, account):
        if account in cls._all_:
            one = cls._all_[account]
        else:
            one = cls._all_[account] = cls()
        return one

    def __init__(self) -> None:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", self.port)) != 0:
                cmd = f'start cmd /c "title Console · 🀄 && {root / "common/endless/mahjong-helper"} -majsoul -p {self.port}"'
                system(cmd)

        self.api = f"https://127.0.0.1:{self.port}"
        self.__class__.port += 1
