import re

from . import logger
from .hook import hooks
from .proto import MsgManager
from mitmproxy import http


gm_msgs = [] # game msgs

def log(mger: MsgManager):
    msg = mger.m
    # logger.info(f"[i][gold1]& {mger.tag} {msg.type.name} {msg.method} {msg.id}")
    # logger.debug(f"[cyan3]# {msg.amended} {msg.data}")

def get_messages():
    return gm_msgs

class WebSocketAddon:
    def __init__(self):
        self.manager = MsgManager()

    # def request(self, flow: http.HTTPFlow):
    #     if flow.request.method == "GET":
    #         if re.search(r'^https://game\.maj\-soul\.(com|net)/[0-9]+/v[0-9\.]+\.w/code\.js$', flow.request.url):
    #             print("====== GET code.js ======"*3)
    #             print("====== GET code.js ======"*3)
    #             print("====== GET code.js ======"*3)
    #             flow.request.url = "http://cdn.jsdelivr.net/gh/Avenshy/majsoul_mod_plus/safe_code.js"
    #         elif re.search(r'^https://game\.mahjongsoul\.com/v[0-9\.]+\.w/code\.js$', flow.request.url):
    #             flow.request.url = "http://cdn.jsdelivr.net/gh/Avenshy/majsoul_mod_plus/safe_code.js"
    #         elif re.search(r'^https://mahjongsoul\.game\.yo-star\.com/v[0-9\.]+\.w/code\.js$', flow.request.url):
    #             flow.request.url = "http://cdn.jsdelivr.net/gh/Avenshy/majsoul_mod_plus/safe_code.js"

    def websocket_start(self, flow: http.HTTPFlow):
        logger.info(" ".join(["[i][green]Connected", flow.id[:13]]))

    def websocket_end(self, flow: http.HTTPFlow):
        logger.info(" ".join(["[i][blue]Disconnected", flow.id[:13]]))

    def websocket_message(self, flow: http.HTTPFlow):
        # make type checker happy
        assert flow.websocket is not None

        try:
            self.manager.parse(flow)
        except:
            logger.warning(" ".join(["[i][red]Unsupported Message @", flow.id[:13]]))
            logger.debug(__import__("traceback").format_exc())

            return
        
        global gm_msgs
        gm_msgs.append(self.manager.m)

        if self.manager.member:
            for hook in hooks:
                try:
                    hook.hook(self.manager)
                except:
                    # logger.warning(" ".join(["[i][red]Error", self.manager.m.method]))
                    logger.debug(__import__("traceback").format_exc())

            if self.manager.m.amended:
                self.manager.apply()

        log(self.manager)


addons = [WebSocketAddon()]
