from mitmproxy import http

from . import conf
from .proto.liqi import Msg, MsgType

events = {}


def listen(*key):
    def decorator(func):
        if key in events:
            events[key].append(func)
        else:
            events[key] = [func]

        return func

    return decorator


# mark flow with account_id
@listen(MsgType.Res, ".lq.Lobby.login")
@listen(MsgType.Res, ".lq.Lobby.emailLogin")
@listen(MsgType.Res, ".lq.Lobby.oauth2Login")  # login
@listen(MsgType.Req, ".lq.FastTest.authGame")  # new match
def login(flow: http.HTTPFlow, msg: Msg):
    setattr(flow, "account_id", msg.data["account_id"])


# import plugins
if conf["plugin"]["enable_aider"]:
    import mhm.plugin.aider
if conf["plugin"]["enable_chest"]:
    import mhm.plugin.chest
if conf["plugin"]["enable_skins"]:
    import mhm.plugin.skin
