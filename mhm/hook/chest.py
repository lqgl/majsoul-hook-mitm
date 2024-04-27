import random

from mhm.hook import Hook
from mhm.proto import MsgManager, MsgType
from mhm.resource import ResourceManager

POPULATION = ["chara", "skin", "gift"]
# NOTE: Weights of above `POPULATATION`
WEIGHTS = [5, 15, 80]

class EstHook(Hook):
    def __init__(self, resger: ResourceManager) -> None:
        super().__init__()

        @self.bind(MsgType.Res, ".lq.Lobby.login")
        @self.bind(MsgType.Res, ".lq.Lobby.emailLogin")
        @self.bind(MsgType.Res, ".lq.Lobby.oauth2Login")  # login
        @self.bind(MsgType.Res, ".lq.Lobby.fetchAccountInfo")  # lobby refresh
        def _(mger: MsgManager):
            mger.data["account"]["platform_diamond"] = [{"id": 100001, "count": 66666}]
            mger.amend()

        @self.bind(MsgType.Req, ".lq.Lobby.openChest")
        def _(mger: MsgManager):
            chest = resger.chest_map[mger.data["chest_id"]]
            count = mger.data["count"]
            # HACK: Currently UP and NORMAL chests are mixed
            mger.respond(
                {
                    "results": [
                        {
                            "reward": {"count": 1, "id": random.choice(chest[k])},
                        }
                        for k in random.choices(POPULATION, WEIGHTS, k=count)
                    ],
                    "total_open_count": count,
                }
            )