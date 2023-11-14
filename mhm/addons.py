from mitmproxy import http


from . import logger, conf
from .events import events
from .proto.liqi import Proto, Msg, MsgType


class WebSocketAddon:
    def __init__(self):
        self.proto = Proto()

    def websocket_start(self, flow: http.HTTPFlow):
        logger.info(" ".join(["[i][green]Connected", flow.id[:13]]))

    def websocket_end(self, flow: http.HTTPFlow):
        logger.info(" ".join(["[i][blue]Disconnected", flow.id[:13]]))

    def websocket_message(self, flow: http.HTTPFlow):
        # make type checker happy
        assert flow.websocket is not None

        try:
            msg = self.proto.parse(flow)
        except:
            logger.warning(" ".join(["[i][red]Unsupported Message @", flow.id[:13]]))
            logger.debug(__import__("traceback").format_exc())

            return

        handle(flow, msg)


addons = [WebSocketAddon()]


def log(flow: http.HTTPFlow, msg: Msg):
    tag = str(flow.account_id) if hasattr(flow, "account_id") else flow.id[:13]

    logger.info(" ".join(["[i][gold1]&", tag, msg.type.name, msg.method, str(msg.id)]))
    logger.debug(msg)


def handle(flow: http.HTTPFlow, msg: Msg):
    for func in [
        *events.get(msg.key, []),
        *events.get(any, []),
    ]:
        try:
            func(flow, msg)
        except:
            logger.warning(" ".join(["[i][red]Error", flow.id[:13]]))
            logger.debug(__import__("traceback").format_exc())

    if msg.amended:
        msg.apply(flow)

    log(flow, msg)
