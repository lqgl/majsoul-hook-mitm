import asyncio
import time
import threading

from . import pRoot, conf, resver, init
from pathlib import Path
from playwright.sync_api import sync_playwright
from loguru import logger

from typing import Any, Coroutine
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.events import Event
from textual.widgets import (Button, Checkbox, Footer, Header, Label, LoadingIndicator, Pretty)
from mhm.action import Action
from mhm.majsoul2mjai import MajsoulBridge
from mhm.action import get_click_list, get_autohu
from mhm.addons import get_messages
from mhm.libriichi_helper import meta_to_recommend, state_to_tehai
from mhm.tileUnicode import TILE_2_UNICODE_ART_RICH, VERTICLE_RULE, HAI_VALUE
from mhm.proto import MsgType


PROXINJECTOR = pRoot / "common/proxinject/proxinjector-cli"
ENABLE_PLAYWRIGHT = False
AUTOPLAY = False
AUTO_NEXT_GAME = False

AUTO_GAME = {
    "endGameStage": [
        (14.75, 8.3375),    # 点击确定按钮
        (6.825, 6.8),       # 点击好感度礼物
        (11.5, 2.75),       # 点击段位场
    ],
    "rankStage": [
        (11.5, 6.15),  # 金之间: gold
        (11.5, 4.825), # 银之间: silver
        (11.5, 3.375), # 铜之间: copper
        (11.5, 5.425), # 玉之间: jade
        (11.5, 6.825), # 王座之间: king
    ],
    "roomsAndRoundsStage": [
        (11.5, 4.7625), # 四人南
        (11.5, 3.475),  # 四人东
        (11.5, 6.15),   # 移动位置点
        (11.5, 6.5625), # 三人南
        (11.5, 5.4),    # 三人东
    ],
}

def _cmd(dict):
    return [obj for key, value in dict.items() for obj in (f"--{key}", value)]


async def start_proxy():
    from mitmproxy.tools.dump import DumpMaster
    from mitmproxy.options import Options
    from .addons import addons

    master = DumpMaster(Options(**conf.mitmdump), **conf.dump)
    master.addons.add(*addons)
    await master.run()
    return master


async def start_inject():
    cmd = [PROXINJECTOR, *_cmd(conf.proxinject)]

    while True:
        process = await asyncio.subprocess.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        await asyncio.sleep(0.8)


game_end_msgs = []

def get_end_msgs():
    return game_end_msgs

def start_playwright():
    playwright_width = conf.playwright['width']
    playwright_height = conf.playwright['height']
    scale = playwright_width / 16
    playwrightContextManager = sync_playwright()
    playwright = playwrightContextManager.__enter__()
    chromium = playwright.chromium
    browser = chromium.launch_persistent_context(
    user_data_dir=Path(__file__).parent.parent / 'data',
    headless=False,
    viewport={'width': playwright_width, 'height': playwright_height},
    proxy={"server": "http://localhost:7878"},
    ignore_default_args=['--enable-automation'])

    page = browser.new_page()

    page.goto('https://game.maj-soul.com/1/')
    # https://stackoverflow.com/questions/73209567/close-or-switch-tabs-in-playwright-python
    all_pages = page.context.pages
    all_pages[0].close()

    while True:
        if len(game_end_msgs) > 0:
            parse_msg = game_end_msgs.pop(0)
            if AUTO_NEXT_GAME:
                if parse_msg['method'] == '.lq.NotifyGameEndResult':
                    time.sleep(30)
                    xy_scale = {"x": AUTO_GAME['endGameStage'][0][0] * scale,
                                "y": AUTO_GAME['endGameStage'][0][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(1)
                    page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    time.sleep(5)
                    page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    time.sleep(10)
                    xy_scale = {"x": AUTO_GAME['endGameStage'][1][0] * scale,
                                "y": AUTO_GAME['endGameStage'][1][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(1)
                    page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    time.sleep(5)
                    xy_scale = {"x": AUTO_GAME['endGameStage'][0][0] * scale,
                                "y": AUTO_GAME['endGameStage'][0][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(1)
                    page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    time.sleep(5)
                    xy_scale = {"x": AUTO_GAME['endGameStage'][2][0] * scale,
                                "y": AUTO_GAME['endGameStage'][2][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    print(f"page_clicker_next_game: {xy_scale}")
                    time.sleep(2)
                elif parse_msg['method'] == '.lq.NotifyGameTerminate':
                    time.sleep(8)
                    xy_scale = {"x": AUTO_GAME['endGameStage'][2][0] * scale,
                                "y": AUTO_GAME['endGameStage'][2][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    print(f"page_clicker_next_game: {xy_scale}")
                    time.sleep(2)

                if parse_msg['method'] == '.lq.NotifyGameEndResult' or parse_msg[
                    'method'] == '.lq.NotifyGameTerminate':
                    if conf.autoNextGame.next_game_Rank == 'gold':
                        xy_scale = {"x": AUTO_GAME['rankStage'][0][0] * scale,
                                    "y": AUTO_GAME['rankStage'][0][1] * scale}
                        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                        time.sleep(0.5)
                        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                        print(f"page_clicker_next_game_gold: {xy_scale}")
                        time.sleep(2)
                    elif conf.autoNextGame.next_game_Rank == 'silver':
                        xy_scale = {"x": AUTO_GAME['rankStage'][1][0] * scale,
                                    "y": AUTO_GAME['rankStage'][1][1] * scale}
                        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                        time.sleep(0.5)
                        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                        print(f"page_clicker_next_game_silver: {xy_scale}")
                        time.sleep(2)
                    elif conf.autoNextGame.next_game_Rank == 'copper':
                        xy_scale = {"x": AUTO_GAME['rankStage'][2][0] * scale,
                                    "y": AUTO_GAME['rankStage'][2][1] * scale}
                        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                        time.sleep(0.5)
                        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                        print(f"page_clicker_next_game_copper: {xy_scale}")
                        time.sleep(2)
                    elif conf.autoNextGame.next_game_Rank == 'jade':
                        xy_scale = {"x": AUTO_GAME['rankStage'][0][0] * scale,
                                    "y": AUTO_GAME['rankStage'][0][1] * scale}
                        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                        time.sleep(0.5)
                        page.mouse.wheel(0, 100)
                        page.mouse.wheel(0, 100)
                        page.mouse.wheel(0, 100)
                        page.mouse.wheel(0, 100)
                        time.sleep(2)
                        xy_scale = {"x": AUTO_GAME['rankStage'][3][0] * scale,
                                    "y": AUTO_GAME['rankStage'][3][1] * scale}
                        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                        time.sleep(0.5)
                        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                        print(f"page_clicker_next_game_jade: {xy_scale}")
                        time.sleep(2)
                    elif conf.autoNextGame.next_game_Rank == 'king':
                        xy_scale = {"x": AUTO_GAME['rankStage'][0][0] * scale,
                                    "y": AUTO_GAME['rankStage'][0][1] * scale}
                        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                        time.sleep(0.5)
                        page.mouse.wheel(0, 100)
                        page.mouse.wheel(0, 100)
                        page.mouse.wheel(0, 100)
                        page.mouse.wheel(0, 100)
                        time.sleep(2)
                        xy_scale = {"x": AUTO_GAME['rankStage'][4][0] * scale,
                                    "y": AUTO_GAME['rankStage'][4][1] * scale}
                        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                        time.sleep(0.5)
                        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                        print(f"page_clicker_next_game_king: {xy_scale}")
                        time.sleep(2)

                    if conf.autoNextGame.next_game_number == '4p':
                        if conf.autoNextGame.next_game_rounds == 'south':
                            xy_scale = {"x": AUTO_GAME['roomsAndRoundsStage'][0][0] * scale,
                                        "y": AUTO_GAME['roomsAndRoundsStage'][0][1] * scale}
                            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                            time.sleep(0.5)
                            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                            print(f"page_clicker_next_game_4p_south: {xy_scale}")
                            time.sleep(1)
                        elif conf.autoNextGame.next_game_rounds == 'east':
                            xy_scale = {"x": AUTO_GAME['roomsAndRoundsStage'][1][0] * scale,
                                        "y": AUTO_GAME['roomsAndRoundsStage'][1][1] * scale}
                            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                            time.sleep(0.5)
                            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                            print(f"page_clicker_next_game_4p_east: {xy_scale}")
                            time.sleep(1)
                    elif conf.autoNextGame.next_game_number == '3p':
                        if conf.autoNextGame.next_game_rounds == 'south':
                            xy_scale = {"x": AUTO_GAME['rankStage'][2][0] * scale,
                                        "y": AUTO_GAME['rankStage'][2][1] * scale}
                            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                            time.sleep(0.5)
                            page.mouse.wheel(0, 100)
                            page.mouse.wheel(0, 100)
                            page.mouse.wheel(0, 100)
                            page.mouse.wheel(0, 100)
                            time.sleep(2)
                            xy_scale = {"x": AUTO_GAME['roomsAndRoundsStage'][3][0] * scale,
                                        "y": AUTO_GAME['roomsAndRoundsStage'][3][1] * scale}
                            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                            time.sleep(0.5)
                            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                            print(f"page_clicker_next_game_3p_south: {xy_scale}")
                            time.sleep(1)
                        elif conf.autoNextGame.next_game_rounds == 'east':
                            xy_scale = {"x": AUTO_GAME['rankStage'][2][0] * scale,
                                        "y": AUTO_GAME['rankStage'][2][1] * scale}
                            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                            time.sleep(0.5)
                            page.mouse.wheel(0, 100)
                            page.mouse.wheel(0, 100)
                            page.mouse.wheel(0, 100)
                            page.mouse.wheel(0, 100)
                            time.sleep(2)
                            xy_scale = {"x": AUTO_GAME['roomsAndRoundsStage'][4][0] * scale,
                                        "y": AUTO_GAME['roomsAndRoundsStage'][4][1] * scale}
                            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                            time.sleep(0.5)
                            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                            print(f"page_clicker_next_game_3p_east: {xy_scale}")
                            time.sleep(1)
        click_list = get_click_list()
        if len(click_list) > 0:
            xy = click_list.pop(0)
            xy_scale = {"x":xy[0]*scale,"y":xy[1]*scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.1)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            print(f"page_clicker: {xy_scale}")
            do_autohu = get_autohu()
            if do_autohu:
                # print(f"do_autohu")
                page.evaluate("() => view.DesktopMgr.Inst.setAutoHule(true)")
                # page.locator("#layaCanvas").click(position=xy_scale)
                do_autohu = False
        else:
            time.sleep(1)  # thread will block here

class Akagi(App):
    CSS_PATH = "client.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.action = Action()
        self.bridge = MajsoulBridge()
        self.consume_ids = []
        self.latest_operation_list = None
        self.gm_msg_list = []
        self.mjai_msg_list = []
        self.isLiqi = False
        self.needOperate = False

    def on_mount(self) -> None:
        self.game_log = self.query_one("#game_log")
        self.mjai_log = self.query_one("#mjai_log")
        self.akagi_action = self.query_one("#akagi_action")
        self.akagi_pai = self.query_one("#akagi_pai")
        self.pai_unicode_art = self.query_one("#pai_unicode_art")
        self.akagi_container = self.query_one("#akagi_container")
        self.game_log.update(self.gm_msg_list)
        self.mjai_log.update(self.mjai_msg_list)
        self.game_log_container = self.query_one("#game_log_container")
        self.mjai_log_container = self.query_one("#mjai_log_container")
        self.tehai_labels = [self.query_one("#tehai_"+str(i)) for i in range(13)]
        self.tehai_value_labels = [self.query_one("#tehai_value_"+str(i)) for i in range(13)]
        self.tehai_rule = self.query_one("#tehai_rule")
        self.tsumohai_label = self.query_one("#tsumohai")
        self.tsumohai_value_label = self.query_one("#tsumohai_value")
        self.tehai_container = self.query_one("#tehai_container")
        self.game_log_container.scroll_end(animate=False)
        self.mjai_log_container.scroll_end(animate=False)
        self.akagi_action.label = "Akagi"
        self.update_msgs = self.set_interval(0.10, self.get_messages)

    def update_containers(self):
        # log
        self.gm_msg_list = []
        self.mjai_msg_list = []
        self.game_log.update(self.gm_msg_list)
        self.mjai_log.update(self.mjai_msg_list)
        # tehai
        for idx, tehai_label in enumerate(self.tehai_labels):
            tehai_label.update(TILE_2_UNICODE_ART_RICH["?"])
        for idx, tehai_value_label in enumerate(self.tehai_value_labels):
            tehai_value_label.update(HAI_VALUE[40])
        self.tsumohai_label.update(TILE_2_UNICODE_ART_RICH["?"])
        self.tsumohai_value_label.update(HAI_VALUE[40])
        # akagi
        self.akagi_action.label = "Akagi"
        for akagi_action_class in self.akagi_action.classes:
            self.akagi_action.remove_class(akagi_action_class)
        self.akagi_pai.label = "None"
        for akagi_pai_class in self.akagi_pai.classes:
            self.akagi_pai.remove_class(akagi_pai_class)
        self.pai_unicode_art.update(TILE_2_UNICODE_ART_RICH["?"])

    def get_messages(self):
        gm_msgs = get_messages()
        if len(gm_msgs) > 0:
            gm_msg = gm_msgs.pop(0)
            parse_msg = {'id': gm_msg.id, 'type': gm_msg.type, 'method': gm_msg.method, 'data': gm_msg.data}
            # game log container
            self.gm_msg_list.append(parse_msg)
            self.game_log.update(self.gm_msg_list[-1])
            self.game_log_container.scroll_end(animate=False)

            if gm_msg.method == '.lq.ActionPrototype':
                if 'operation' in gm_msg.data.get('data'):
                    if 'operation_list' in gm_msg.data.get('data').get('operation'):
                        self.needOperate = True
                        self.action.latest_operation_list = gm_msg.data.get('data').get('operation').get('operation_list')
                if gm_msg.data.get('name') == 'ActionDiscardTile':
                    self.action.isNewRound = False
                    if gm_msg.data.get('data').get('isLiqi'):
                        self.isLiqi = True
                if gm_msg.data.get('name') == 'ActionNewRound':
                    self.action.isNewRound = True
                    self.action.reached = False
            if gm_msg.method == '.lq.FastTest.inputOperation' or gm_msg.method == '.lq.FastTest.inputChiPengGang':
                if gm_msg.type == MsgType.Req:
                    self.needOperate = False
                    self.gm_msg_list = []
                    self.mjai_msg_list = []
                    self.isLiqi = False
            
            # 游戏结束
            if parse_msg['method'] == '.lq.NotifyGameEndResult' or parse_msg['method'] == '.lq.NotifyGameTerminate':
                global game_end_msgs
                game_end_msgs.append(parse_msg)
                self.update_containers()

            # 对局结束
            if parse_msg['data'].get('name') == 'ActionHule' or parse_msg['data'].get('name') == 'ActionNoTile' or parse_msg['data'].get('name') == 'ActionLiuJu':
                self.update_containers()
                
            # process game message.
            mjai_msg = self.bridge.input(parse_msg)
            if mjai_msg is not None:
                if self.bridge.reach and mjai_msg["type"] == "dahai":
                    mjai_msg["type"] = "reach"
                    self.bridge.reach = False
                # mjai log container
                mjai_msg['meta'] = meta_to_recommend(mjai_msg['meta'])
                player_state = self.bridge.mjai_client.bot.state()
                tehai, tsumohai = state_to_tehai(player_state)
                for idx, tehai_label in enumerate(self.tehai_labels):
                    tehai_label.update(TILE_2_UNICODE_ART_RICH[tehai[idx]])
                action_list = [x[0] for x in mjai_msg['meta']]
                for idx, tehai_value_label in enumerate(self.tehai_value_labels):
                    # latest_mjai_msg['meta'] is list of (pai, value)
                    try:
                        pai_value = int(mjai_msg['meta'][action_list.index(tehai[idx])][1] * 40)
                        if pai_value == 40:
                            pai_value = 39
                    except ValueError:
                        pai_value = 40
                    tehai_value_label.update(HAI_VALUE[pai_value])
                self.tsumohai_label.update(TILE_2_UNICODE_ART_RICH[tsumohai])
                if tsumohai in action_list:
                    try:
                        pai_value = int(mjai_msg['meta'][action_list.index(tsumohai)][1] * 40)
                        if pai_value == 40:
                            pai_value = 39
                    except ValueError:
                        pai_value = 40
                    self.tsumohai_value_label.update(HAI_VALUE[pai_value])
                # mjai log container
                self.mjai_msg_list.append(mjai_msg)
                self.mjai_log.update(self.mjai_msg_list[-1])
                self.mjai_log_container.scroll_end(animate=False)
                self.akagi_action.label = mjai_msg["type"]
                for akagi_action_class in self.akagi_action.classes:
                    self.akagi_action.remove_class(akagi_action_class)
                self.akagi_action.add_class("action_"+mjai_msg["type"])
                for akagi_pai_class in self.akagi_pai.classes:
                    self.akagi_pai.remove_class(akagi_pai_class)
                self.akagi_pai.add_class("pai_"+mjai_msg["type"])
                if "consumed" in mjai_msg:
                    self.akagi_pai.label = str(mjai_msg["consumed"])
                    if "pai" in mjai_msg:
                        self.pai_unicode_art.update(TILE_2_UNICODE_ART_RICH[mjai_msg["pai"]])
                    self.akagi_container.mount(Label(VERTICLE_RULE, id="consumed_rule"))
                    self.consume_ids.append("#"+"consumed_rule")
                    i=0
                    for c in mjai_msg["consumed"]:
                        self.akagi_container.mount(Label(TILE_2_UNICODE_ART_RICH[c], id="consumed_"+c+str(i)))
                        self.consume_ids.append("#"+"consumed_"+c+str(i))
                        i+=1
                elif "pai" in mjai_msg:
                    for consume_id in self.consume_ids:
                        self.query_one(consume_id).remove()
                    self.consume_ids = []
                    self.akagi_pai.label = str(mjai_msg["pai"])
                    self.pai_unicode_art.update(TILE_2_UNICODE_ART_RICH[mjai_msg["pai"]])
                else:
                    self.akagi_pai.label = "None"
                    self.pai_unicode_art.update(TILE_2_UNICODE_ART_RICH["?"])
                self.tehai = tehai
                self.tsumohai = tsumohai

                # 自动打牌
                if AUTOPLAY and self.needOperate:
                    self.action.mjai2action(self.mjai_msg_list[-1], self.tehai, self.tsumohai, self.isLiqi)
        # 出牌验证
        elif AUTOPLAY and self.needOperate and len(self.mjai_msg_list) > 0:
            self.action.mjai2action(self.mjai_msg_list[-1], self.tehai, self.tsumohai, self.isLiqi)
        else:
            time.sleep(1)


    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        game_log_container = ScrollableContainer(Pretty(self.gm_msg_list, id="game_log"), id="game_log_container")
        mjai_log_container = ScrollableContainer(Pretty(self.mjai_msg_list, id="mjai_log"), id="mjai_log_container")
        log_container = Horizontal(game_log_container, mjai_log_container, id="log_container")
        game_log_container.border_title = "GameProto"
        mjai_log_container.border_title = "Mjai"
        tehai_labels = [Label(TILE_2_UNICODE_ART_RICH["?"], id="tehai_"+str(i)) for i in range(13)]
        tehai_value_labels = [Label(HAI_VALUE[40], id="tehai_value_"+str(i)) for i in range(13)]
        tehai_rule = Label(VERTICLE_RULE, id="tehai_rule")
        tsumohai_label = Label(TILE_2_UNICODE_ART_RICH["?"], id="tsumohai")
        tsumohai_value_label = Label(HAI_VALUE[40], id="tsumohai_value")
        tehai_container = Horizontal(id="tehai_container")
        for i in range(13):
            tehai_container.mount(tehai_labels[i])
            tehai_container.mount(tehai_value_labels[i])
        tehai_container.mount(tehai_rule)
        tehai_container.mount(tsumohai_label)
        tehai_container.mount(tsumohai_value_label)
        tehai_container.border_title = "Tehai"
        akagi_action = Button("Akagi", id="akagi_action", variant="default")
        akagi_pai    = Button("Pai", id="akagi_pai", variant="default")
        pai_unicode_art = Label(TILE_2_UNICODE_ART_RICH["?"], id="pai_unicode_art")
        akagi_container = Horizontal(akagi_action, akagi_pai, pai_unicode_art, id="akagi_container")
        akagi_container.border_title = "Akagi"
        loading_indicator = LoadingIndicator(id="loading_indicator")
        loading_indicator.styles.height = "3"
        checkbox_autoplay = Checkbox("Autoplay", id="checkbox_autoplay", classes="short", value=AUTOPLAY)
        checkbox_autonext = Checkbox("AutoNextGame", id="checkbox_autonext", classes="short", value=AUTO_NEXT_GAME)
        checkbox_container = Vertical(checkbox_autoplay, checkbox_autonext, id="checkbox_container")
        checkbox_container.border_title = "Options"
        bottom_container = Horizontal(checkbox_container, akagi_container, id="bottom_container")
        yield Header()
        yield Footer()
        yield log_container
        yield tehai_container
        yield bottom_container

    def on_event(self, event: Event) -> Coroutine[Any, Any, None]:
        return super().on_event(event)

    @on(Checkbox.Changed, "#checkbox_autoplay")
    def checkbox_autoplay_changed(self, event: Checkbox.Changed) -> None:
        global AUTOPLAY
        AUTOPLAY = event.value
        pass

    @on(Checkbox.Changed, "#checkbox_autonext")
    def checkbox_autonext_changed(self, event: Checkbox.Changed) -> None:
        global AUTO_NEXT_GAME
        AUTO_NEXT_GAME = event.value
        pass

    def action_quit(self) -> None:
        self.update_msgs.stop()
        self.exit()


def main():
    async def start():
        logger.info(f"[i]log level: {conf.mhm.log_level}")
        logger.info(f"[i]pure python protobuf: {conf.mhm.pure_python_protobuf}")

        logger.info(f"[i]version: {resver.version}")
        logger.info(f"[i]characters: {len(resver.emotes)}")

        logger.info(f"[i]auto next game: {conf.autoNextGame.enable_auto_next_game} Rank: {conf.autoNextGame.next_game_Rank} Number: {conf.autoNextGame.next_game_number} Rounds: {conf.autoNextGame.next_game_rounds}")

        tasks = set()

        if conf.mitmdump:
            tasks.add(start_proxy())
            logger.info(f"[i]mitmdump launched @ {len(conf.mitmdump.get('mode'))} mode")

        if conf.proxinject:
            tasks.add(start_inject())
            logger.info(f"[i]proxinject launched @ {conf.proxinject.get('set-proxy')}")

        await asyncio.gather(*tasks)
    # 日志设定
    logger.remove(handler_id=None)
    logger.add("akagi.log", level = "DEBUG")
    # 初始化资源配置
    init()
    try:
        # Create and start the proxy server thread
        proxy_thread = threading.Thread(target=lambda: asyncio.run(start()))
        proxy_thread.daemon = True
        proxy_thread.start()
        # wait for mitmproxy start
        time.sleep(1)

        if conf.playwright["enable"]:
            global ENABLE_PLAYWRIGHT, AUTOPLAY
            ENABLE_PLAYWRIGHT = True
            AUTOPLAY = True
        
        # start playweight thread
        if ENABLE_PLAYWRIGHT:
            playwright_thread = threading.Thread(target=start_playwright)
            playwright_thread.daemon = True
            playwright_thread.start()

        # start texual terminal
        app = Akagi()
        app.run()
    except KeyboardInterrupt:
        exit(0)
