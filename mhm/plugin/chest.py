from random import random, choice

from mhm import resver
from mhm.events import manager
from mhm.proto.liqi import Msg, MsgType

DEFAULT_CHEST = [
    # CHARACTERS
    (0.05, list(range(200003, resver.max_charid - 1))),
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


# login
@manager.register(MsgType.Res, ".lq.Lobby.login")
@manager.register(MsgType.Res, ".lq.Lobby.emailLogin")
@manager.register(MsgType.Res, ".lq.Lobby.oauth2Login")
# lobby refresh
@manager.register(MsgType.Res, ".lq.Lobby.fetchAccountInfo")
def login(msg: Msg):
    msg.data["account"]["platform_diamond"] = [{"id": 100001, "count": 66666}]
    msg.amended = True


@manager.register(MsgType.Req, ".lq.Lobby.openChest")
def openChest(msg: Msg):
    data = chest(msg.data["count"], msg.data["chest_id"])

    msg.drop()
    msg.respond(data).inject()
