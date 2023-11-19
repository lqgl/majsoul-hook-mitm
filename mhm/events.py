from typing import TypeVar

from . import conf, logger
from .proto.liqi import Msg, MsgType


T = TypeVar("T")
K = TypeVar("K", str, int)


class ObjectPool:
    def __init__(self) -> None:
        self.pool: dict[type[T], dict[K, T]] = {}

    def one(self, cls: type[T], key: K, *args, **kwargs) -> T:
        if cls not in self.pool:
            self.pool[cls] = {}
        if key not in self.pool[cls]:
            self.pool[cls][key] = cls(*args, **kwargs)
        return self.pool[cls][key]

    def get(self, cls: type[T], key: K) -> T:
        try:
            return self.pool[cls][key]
        except KeyError:
            return None


pool = ObjectPool()


def log(msg: Msg):
    logger.info(f"[i][gold1]& {msg.tag} {msg.type.name} {msg.method} {msg.id}")
    logger.debug(f"[cyan3]# {msg.amended} {msg.data}")


class EventManager:
    def __init__(self):
        self.events = {}

    def register(self, *key):
        def decorator(func):
            if key in self.events:
                self.events[key].append(func)
            else:
                self.events[key] = [func]
            return func

        return decorator

    def trigger(self, msg: Msg):
        for func in [
            *self.events.get(msg.key, []),
            *self.events.get((any,), []),
        ]:
            try:
                func(msg)
            except:
                logger.warning(" ".join(["[i][red]Error", msg.tag]))
                logger.debug(__import__("traceback").format_exc())

        if msg.amended:
            msg.apply()

        log(msg)


manager = EventManager()


# mark flow with account_id
@manager.register(MsgType.Res, ".lq.Lobby.login")
@manager.register(MsgType.Res, ".lq.Lobby.emailLogin")
@manager.register(MsgType.Res, ".lq.Lobby.oauth2Login")  # login
@manager.register(MsgType.Req, ".lq.FastTest.authGame")  # new match
def login(msg: Msg):
    msg.account = msg.data["account_id"]


# import plugins
if conf.plugin.enable_aider:
    import mhm.plugin.aider
if conf.plugin.enable_chest:
    import mhm.plugin.chest
if conf.plugin.enable_skins:
    import mhm.plugin.skins
