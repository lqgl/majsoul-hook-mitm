from mitmproxy import http


from . import logger
from .events import events
from .proto.liqi import Proto, Msg


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

        handle(msg)


addons = [WebSocketAddon()]


def log(msg: Msg):
    logger.info(f"[i][gold1]& {msg.tag} {msg.type.name} {msg.method} {msg.id}")
    logger.debug(msg)


def handle(msg: Msg):
    for func in [
        *events.get(msg.key, []),
        *events.get((any,), []),
    ]:
        try:
            func(msg)
        except:
            logger.warning(" ".join(["[i][red]Error", msg.tag]))
            logger.debug(__import__("traceback").format_exc())

    if msg.amended:
        msg.apply()

    log(msg)
