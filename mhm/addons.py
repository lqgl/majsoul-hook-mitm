from mitmproxy import http

from .proto.liqi import Proto, Msg, MsgType
from . import logger, conf


def _log(flow: http.HTTPFlow, msg: Msg) -> None:
    logger.info(
        f"[i][gold1]{msg.type.name}[/gold1] [cyan3]{msg.method}[/cyan3] {msg.id}th @ {flow.account_id if hasattr(flow, 'account_id') else flow.id[:13]}",
    )
    logger.debug(
        f"{'-->' if msg.type == MsgType.Req else '<--'} {msg.data} @ {flow.id[:13]}",
    )


class WebSocketAddon:
    proto = Proto()
    players = dict()
    plugins = list()

    if conf["plugin"]["enable_aider"]:
        from .plugin.aider import AiderPlugin

        plugins.append(AiderPlugin)
    if conf["plugin"]["enable_skins"]:
        from .plugin.skin import SkinPlugin

        plugins.append(SkinPlugin)
    if conf["plugin"]["enable_chest"]:
        from .plugin.chest import ChestPlugin

        plugins.append(ChestPlugin)

    def handle(self, flow: http.HTTPFlow, msg: Msg) -> None:
        # mark flow with account_id
        if msg.func in {
            # gateway
            "_lq_Lobby_login_Res",
            "_lq_Lobby_emailLogin_Res",
            "_lq_Lobby_oauth2Login_Res",
            # game-gateway
            "_lq_FastTest_authGame_Req",
        }:
            setattr(flow, "account_id", msg.data["account_id"])

        if hasattr(flow, "account_id"):
            account_id = getattr(flow, "account_id")
            manipulated = 0

            if account_id not in self.players:
                self.players[account_id] = [cls() for cls in self.plugins]

            for plugin in self.players[account_id]:
                # exception handle
                try:
                    manipulated += not plugin.handle(flow, msg)
                except:
                    logger.warning(f"[i][red]{type(plugin)} error at {msg.func}")
                    logger.debug(__import__("traceback").format_exc())

            if manipulated:
                self.proto.manipulate(flow, msg)

    def websocket_start(self, flow: http.HTTPFlow):
        logger.info(f"[i][green]Connected[/green] {flow.id[:13]}[/i]")

    def websocket_end(self, flow: http.HTTPFlow):
        logger.info(f"[i][blue]Disconnected[/blue] {flow.id[:13]}[/i]")

    def websocket_message(self, flow: http.HTTPFlow):
        # make type checker happy
        assert flow.websocket is not None

        try:
            msg = self.proto.parse(flow)
        except:
            logger.warning(f"[i][red]Unsupported[/red] message at {flow.id[:13]}[/i]")
            logger.debug(__import__("traceback").format_exc())

            return

        _log(flow, msg)

        self.handle(flow, msg)


addons = [WebSocketAddon()]
