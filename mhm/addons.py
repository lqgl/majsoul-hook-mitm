import json
from . import console
from .config import config
from .hook import Hook
from .proto import MsgManager
from urllib.parse import urlparse, parse_qs
from mitmproxy import http

activated_flows = []
messages_dict = dict() # flow.id -> Queue[gm_msg]
message_idx = dict() # flow.id -> int

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

def log(debug: bool, mger: MsgManager):
    match mger.m.status:
        case "Md" | "ToMd":
            head = "red"
        case "Dp":
            head = "green4"
        case "Og":
            head = "grey85"

    console.log(
        " ".join(
            [
                f"[{head}]{mger.m.status}[/{head}]",
                f"[grey50]{mger.tag}[/grey50]",
                f"[cyan2]{mger.m.type.name}[/cyan2]",
                f"[gold1]{mger.m.method}[/gold1]",
                f"[cyan3]{mger.m.id}[/cyan3]",
            ]
        )
    )

    if debug:
        console.log(f"-->> {mger.m.data}")

class WebSocketAddon:
    def __init__(self, hooks: list[Hook]):
        self.hooks = hooks
        self.debug = config.base.debug
        self.manager = MsgManager()

    def request(self, flow: http.HTTPFlow):
        parsed_url = urlparse(flow.request.url)
        if parsed_url.hostname == "majsoul-hk-client.cn-hongkong.log.aliyuncs.com":
            qs = parse_qs(parsed_url.query)
            try:
                content = json.loads(qs["content"][0])
                if content["type"] == "re_err":
                    flow.kill()
            except:
                return

    def websocket_start(self, flow: http.HTTPFlow):
        console.log(" ".join(["[i][green]Connected", flow.id[:13]]))
        global activated_flows,messages_dict
        activated_flows.append(flow.id)
        messages_dict[flow.id]=[]

    def websocket_end(self, flow: http.HTTPFlow):
        console.log(" ".join(["[i][blue]Disconnected", flow.id[:13]]))
        global activated_flows,messages_dict
        activated_flows.remove(flow.id)
        messages_dict.pop(flow.id)

    def websocket_message(self, flow: http.HTTPFlow):
        # make type checker happy
        assert flow.websocket is not None

        try:
            self.manager.parse(flow)
        except Exception:
            console.log(f"[red]Unsupported Message @ {flow.id[:13]}")

        global activated_flows,messages_dict
        messages_dict[flow.id].append(self.manager.m)

        if self.manager.member:
            for hook in self.hooks:
                try:
                    self.manager.apply(hook.apply)
                except Exception:
                    console.print_exception()

        log(self.debug, self.manager)