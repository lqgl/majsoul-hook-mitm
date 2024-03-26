import socket

import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from mhm import console
from mhm.hook import Hook
from mhm.proto import MsgManager


class DerHook(Hook):
    def __init__(self) -> None:
        self.pool = {}
        disable_warnings(InsecureRequestWarning)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        if sock.connect_ex(("127.0.0.1", 12121)) == 0:
            console.log("[green]Aider Detected")
            self.open = True
        else:
            console.log("[red]No Aider Detected")
            self.open = False

    def send(self, mger: MsgManager):
        if mger.m.method == ".lq.ActionPrototype":
            if mger.data["name"] == "ActionNewRound":
                mger.data["data"]["md5"] = mger.data["data"]["sha256"][:32]
            send_msg = mger.data["data"]
        elif mger.m.method == ".lq.FastTest.syncGame":
            for action in mger.data["game_restore"]["actions"]:
                if action["name"] == "ActionNewRound":
                    action["data"]["md5"] = action["data"]["sha256"][:32]
            send_msg = {"sync_game_actions": mger.data["game_restore"]["actions"]}
        else:
            send_msg = mger.data
        requests.post("https://127.0.0.1:12121", json=send_msg, verify=0, timeout=1)

    def apply(self, mger: MsgManager):
        if self.open and not mger.m.isReq():
            self.send(mger)