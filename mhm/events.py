from . import conf, logger
from .proto.liqi import Msg, MsgType


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
