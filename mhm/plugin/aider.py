from os import system
from requests import post

from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from socket import socket, AF_INET, SOCK_STREAM
from mitmproxy import http

from mhm import ROOT
from mhm.proto.liqi import Plugin, Msg, MsgType

disable_warnings(InsecureRequestWarning)


class AiderPlugin(Plugin):
    port: int = 43410

    def __init__(self) -> None:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", self.port)) != 0:
                cmd = f'start cmd /c "title Console · 🀄 && {ROOT / "common/endless/mahjong-helper"} -majsoul -p {self.port}"'
                system(cmd)

        self.api = f"https://127.0.0.1:{self.port}"
        self.__class__.port += 1

    def handle(self, flow: http.HTTPFlow, msg: Msg) -> bool:
        if msg.type is not MsgType.Req:
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

            post(self.api, json=send_msg, verify=False)

        return True
