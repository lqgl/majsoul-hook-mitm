import re, json

from . import logger
from .hook import hooks
from .proto import MsgManager
from mitmproxy import http
from urllib.parse import urlparse, parse_qs

activated_flows = []
messages_dict = dict() # flow.id -> Queue[gm_msg]
message_idx = dict() # flow.id -> int

def log(mger: MsgManager):
    msg = mger.m
    # logger.info(f"[i][gold1]& {mger.tag} {msg.type.name} {msg.method} {msg.id}")
    # logger.debug(f"[cyan3]# {msg.amended} {msg.data}")

def get_messages(flow_id):
    try:
        idx = message_idx[flow_id]
    except KeyError:
        message_idx[flow_id] = 0
        idx = 0
    if (flow_id not in activated_flows) or (len(messages_dict[flow_id])==0) or (message_idx[flow_id]>=len(messages_dict[flow_id])):
        return None
    msg = messages_dict[flow_id][idx]
    message_idx[flow_id] += 1
    return msg

def get_activated_flows():
    return activated_flows

class WebSocketAddon:
    def __init__(self):
        self.manager = MsgManager()

    def request(self, flow: http.HTTPFlow):
        parsed_url = urlparse(flow.request.url)
        if parsed_url.hostname == "majsoul-hk-client.cn-hongkong.log.aliyuncs.com":
            qs = parse_qs(parsed_url.query)
            try:
                content = json.loads(qs["content"][0])
                if content["type"] == "re_err":
                    logger.warning(" ".join(["[i][red]Error", str(qs)]))
                    flow.kill()
                else:
                    logger.debug(" ".join(["[i][green]Log", str(qs)]))
            except:
                return

    def websocket_start(self, flow: http.HTTPFlow):
        logger.info(" ".join(["[i][green]Connected", flow.id[:13]]))
        global activated_flows,messages_dict
        
        activated_flows.append(flow.id)
        messages_dict[flow.id]=[]

    def websocket_end(self, flow: http.HTTPFlow):
        logger.info(" ".join(["[i][blue]Disconnected", flow.id[:13]]))
        global activated_flows,messages_dict
        activated_flows.remove(flow.id)
        messages_dict.pop(flow.id)

    def websocket_message(self, flow: http.HTTPFlow):
        # make type checker happy
        assert flow.websocket is not None

        try:
            self.manager.parse(flow)
        except:
            logger.warning(" ".join(["[i][red]Unsupported Message @", flow.id[:13]]))
            logger.debug(__import__("traceback").format_exc())

            return
        
        global activated_flows,messages_dict
        messages_dict[flow.id].append(self.manager.m)

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
