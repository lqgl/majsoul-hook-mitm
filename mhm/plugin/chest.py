from mitmproxy import http
from random import random, choice

from mhm import conf
from mhm.proto.liqi import Plugin, Msg

DEFAULT_CHEST = [
    # CHARACTERS
    (0.05, list(range(200003, conf["server"]["max_charid"] - 1))),
    # VIEWS
    (0.2, list(set(range(305001, 305056)).difference({305043, 305047}))),
    # GIFTS
    (1, list(range(303012, 303090, 10))),
]

CHESTS = {
    1005: [
        (0.2, [200076]),
        (0, []),
        (0.0625, list(range(303013, 303090, 10))),
    ],
    -999: [
        (0, []),
        (0, []),
        (0.0625, list(range(303013, 303090, 10))),
    ],
}


def rewards(count: int, chest_id: int):
    rewards = []

    if not chest_id in CHESTS:
        chest_id = -999

    for i in range(0, count):
        random_a = random()
        random_b = random()

        for m in range(0, len(DEFAULT_CHEST)):
            prob_a, pool_a = DEFAULT_CHEST[m]

            if random_a < prob_a:
                prob_b, pool_b = CHESTS[chest_id][m]
                rewards.append(choice(pool_b if random_b < prob_b else pool_a))
                break

    return [{"reward": {"id": id, "count": 1}} for id in rewards]


def chest(count: int, chest_id: int):
    return {
        "results": rewards(count, chest_id),
        "total_open_count": count,
    }


class ChestPlugin(Plugin):
    def _lq_Lobby_fetchAccountInfo_Res(self, flow: http.HTTPFlow, msg: Msg) -> bool:
        return self._lq_Lobby_login_Res(flow, msg)

    def _lq_Lobby_oauth2Login_Res(self, flow: http.HTTPFlow, msg: Msg) -> bool:
        return self._lq_Lobby_login_Res(flow, msg)

    def _lq_Lobby_emailLogin_Res(self, flow: http.HTTPFlow, msg: Msg) -> bool:
        return self._lq_Lobby_login_Res(flow, msg)

    def _lq_Lobby_login_Res(self, flow: http.HTTPFlow, msg: Msg) -> bool:
        msg.data["account"]["platform_diamond"] = [{"id": 100001, "count": 66666}]

    def _lq_Lobby_openChest_Req(self, flow: http.HTTPFlow, msg: Msg) -> bool:
        return super().reply(flow, msg, chest(msg.data["count"], msg.data["chest_id"]))
