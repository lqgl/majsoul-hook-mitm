from typing import Any, Coroutine
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.events import Event, ScreenResume
from textual.screen import Screen
from textual.widgets import (Button, Checkbox, Footer, Header, Input, Label,
                             LoadingIndicator, Log, Markdown, Pretty, Rule,
                             Static)
import json
import random
from .action import Action
from .majsoul2mjai import MajsoulBridge
from .addons import get_messages,get_activated_flows
from .libriichi_helper import meta_to_recommend, state_to_tehai
from .tileUnicode import TILE_2_UNICODE_ART_RICH, VERTICLE_RULE, HAI_VALUE
from .proto import MsgType, Tool
from .config import config
from loguru import logger

game_msgs = []
ENABLEPLAYWRIGHT = False
AUTOPLAY = False
AUTONEXT = False

TILES = [
    "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
    "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
    "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
    "E",  "S",  "W",  "N",  "P",  "F",  "C",
    '5mr', '5pr', '5sr'
]

def get_game_msgs():
    return game_msgs

def get_auto_next():
    return AUTONEXT

class FlowScreen(Screen):

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, flow_id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.flow_id = flow_id
        self.gm_msg_idx = 0
        self.mjai_msg_idx = 0
        self.consume_ids = []
        self.latest_operation_list = None
        self.syncing = True
        self.action = Action()
        self.tehai = ["?"]*13
        self.tsumohai = "?"
        self.isOtherLiqi = False # 是否有人立直
        self.dahai_verfication_job = None

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        game_log_container = ScrollableContainer(Pretty(self.app.gm_msg_dict[self.flow_id], id="game_log"), id="game_log_container")
        mjai_log_container = ScrollableContainer(Pretty(self.app.mjai_msg_dict[self.flow_id], id="mjai_log"), id="mjai_log_container")
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
        checkbox_autonext = Checkbox("AutoNext", id="checkbox_autonext", classes="short", value=AUTONEXT)
        checkbox_container = Vertical(checkbox_autoplay, checkbox_autonext, id="checkbox_container")
        checkbox_container.border_title = "Options"
        bottom_container = Horizontal(checkbox_container, akagi_container, id="bottom_container")
        yield Header()
        yield Footer()
        yield loading_indicator
        yield log_container
        yield tehai_container
        yield bottom_container

    def on_mount(self) -> None:
        self.game_log = self.query_one("#game_log")
        self.mjai_log = self.query_one("#mjai_log")
        self.akagi_action = self.query_one("#akagi_action")
        self.akagi_pai = self.query_one("#akagi_pai")
        self.pai_unicode_art = self.query_one("#pai_unicode_art")
        self.akagi_container = self.query_one("#akagi_container")
        self.game_log.update(self.app.gm_msg_dict[self.flow_id])
        self.mjai_log.update(self.app.mjai_msg_dict[self.flow_id])
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
        self.gm_msg_idx = len(self.app.gm_msg_dict[self.flow_id])
        self.mjai_msg_idx = len(self.app.mjai_msg_dict[self.flow_id])
        self.update_log = self.set_interval(0.10, self.refresh_log)
        try:
            self.akagi_action.label = self.app.mjai_msg_dict[self.flow_id][-1]["type"]
            for akagi_action_class in self.akagi_action.classes:
                self.akagi_action.remove_class(akagi_action_class)
            self.akagi_action.add_class("action_"+self.app.mjai_msg_dict[self.flow_id][-1]["type"])
            for akagi_pai_class in self.akagi_pai.classes:
                self.akagi_pai.remove_class(akagi_pai_class)
            self.akagi_pai.add_class("pai_"+self.app.mjai_msg_dict[self.flow_id][-1]["type"])
        except IndexError:
            self.akagi_action.label = "Akagi"

    def reset_containers(self):
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

    def refresh_log(self) -> None:
        if self.flow_id not in self.app.gm_msg_dict and self.flow_id not in self.app.mjai_msg_dict:
            return
        if self.gm_msg_idx < len(self.app.gm_msg_dict[self.flow_id]):
            self.game_log.update(self.app.gm_msg_dict[self.flow_id][-1])
            self.game_log_container.scroll_end(animate=False)
            self.gm_msg_idx += 1
            gm_msg = self.app.gm_msg_dict[self.flow_id][-1]
            # logger.debug(f"gm_msg:{gm_msg}")
            global game_msgs
            if gm_msg['type'] == MsgType.Notify:
                # 操作通知
                if gm_msg['method'] == '.lq.ActionPrototype':
                    # No matter what the action is, as long as we get a new action, we should stop the verification job as it's outdated.
                    self.stop_dahai_verification()
                    if 'operation' in gm_msg['data']['data']:
                        if 'operation_list' in gm_msg['data']['data']['operation']:
                            self.action.latest_operation_list = gm_msg['data']['data']['operation']['operation_list']
                            logger.debug(f"OperationNotify: {gm_msg}")
                    if gm_msg['data']['name'] == 'ActionDiscardTile':
                        self.action.isNewRound = False
                        if gm_msg["data"].get('data').get('is_liqi'):
                            self.isOtherLiqi = True
                        pass
                    if gm_msg['data']['name'] == 'ActionNewRound':
                        self.action.isNewRound = True
                        self.action.reached = False
                  
                # 对局结束
                if gm_msg['data'].get('name') == 'ActionHule' or gm_msg['data'].get('name') == 'ActionNoTile' or gm_msg['data'].get('name') == 'ActionLiuJu':
                    self.reset_containers()
                
                # 游戏结束
                if gm_msg['method'] == '.lq.NotifyGameEndResult' or gm_msg['method'] == '.lq.NotifyGameTerminate':
                    if AUTONEXT:
                        game_msgs.append(gm_msg)
                    self.action_quit()
                if gm_msg['method'] == '.lq.NotifyGameBroadcast':
                    seat = gm_msg['data'].get('seat')
                    emo_str = gm_msg['data'].get('content')
                    self_seat = self.app.bridge[self.flow_id].seat
                    if emo_str is not None:
                        emo = json.loads(emo_str).get('emo')
                        if seat != self_seat:
                            game_msgs.append(gm_msg)
                        logger.info(f"self_seat:{self_seat} recieved seat:{seat}, emo:{emo}")
            # No matter what the type is, as long as we get a new operation, we should stop the verification job as it's outdated.
            if gm_msg['method'] == '.lq.FastTest.inputOperation' or gm_msg['method'] == '.lq.FastTest.inputChiPengGang':
                self.stop_dahai_verification()
                self.isOtherLiqi = False
                logger.debug(f"Send Operation Request: {gm_msg}")
                
        elif self.syncing:
            self.query_one("#loading_indicator").remove()
            self.syncing = False
            if ENABLEPLAYWRIGHT and AUTOPLAY and len(self.app.mjai_msg_dict[self.flow_id]) > 0:
                self.app.set_timer(2, self.autoplay)
        if self.mjai_msg_idx < len(self.app.mjai_msg_dict[self.flow_id]):
            bridge = self.app.bridge[self.flow_id]
            self.app.mjai_msg_dict[self.flow_id][-1]['meta'] = meta_to_recommend(self.app.mjai_msg_dict[self.flow_id][-1]['meta'], bridge.is_3p)
            latest_mjai_msg = self.app.mjai_msg_dict[self.flow_id][-1]
            # Lose weight
            if config.playwright.lose_weight and latest_mjai_msg is not None:
                latest_mjai_msg = self.lose_weight(latest_mjai_msg)
            # Update tehai
            player_state = bridge.mjai_client.bot.state()
            tehai, tsumohai = state_to_tehai(player_state)
            for idx, tehai_label in enumerate(self.tehai_labels):
                tehai_label.update(TILE_2_UNICODE_ART_RICH[tehai[idx]])
            action_list = [x[0] for x in latest_mjai_msg['meta']]
            for idx, tehai_value_label in enumerate(self.tehai_value_labels):
                # latest_mjai_msg['meta'] is list of (pai, value)
                try:
                    pai_value = int(latest_mjai_msg['meta'][action_list.index(tehai[idx])][1] * 40)
                    if pai_value == 40:
                        pai_value = 39
                except ValueError:
                    pai_value = 40
                tehai_value_label.update(HAI_VALUE[pai_value])
            self.tsumohai_label.update(TILE_2_UNICODE_ART_RICH[tsumohai])
            if tsumohai in action_list:
                try:
                    pai_value = int(latest_mjai_msg['meta'][action_list.index(tsumohai)][1] * 40)
                    if pai_value == 40:
                        pai_value = 39
                except ValueError:
                    pai_value = 40
                self.tsumohai_value_label.update(HAI_VALUE[pai_value])
            # mjai log
            self.mjai_log.update(self.app.mjai_msg_dict[self.flow_id][-3:])
            self.mjai_log_container.scroll_end(animate=False)
            self.mjai_msg_idx += 1
            self.akagi_action.label = latest_mjai_msg["type"]
            for akagi_action_class in self.akagi_action.classes:
                self.akagi_action.remove_class(akagi_action_class)
            self.akagi_action.add_class("action_"+latest_mjai_msg["type"])
            for akagi_pai_class in self.akagi_pai.classes:
                self.akagi_pai.remove_class(akagi_pai_class)
            self.akagi_pai.add_class("pai_"+latest_mjai_msg["type"])
            for consume_id in self.consume_ids:
                self.query_one(consume_id).remove()
            if "consumed" in latest_mjai_msg:
                self.akagi_pai.label = str(latest_mjai_msg["consumed"])
                if "pai" in latest_mjai_msg:
                    self.pai_unicode_art.update(TILE_2_UNICODE_ART_RICH[latest_mjai_msg["pai"]])
                self.akagi_container.mount(Label(VERTICLE_RULE, id="consumed_rule"))
                self.consume_ids.append("#"+"consumed_rule")
                i=0
                for c in latest_mjai_msg["consumed"]:
                    self.akagi_container.mount(Label(TILE_2_UNICODE_ART_RICH[c], id="consumed_"+c+str(i)))
                    self.consume_ids.append("#"+"consumed_"+c+str(i))
                    i+=1
            elif "pai" in latest_mjai_msg:
                self.consume_ids = []
                self.akagi_pai.label = str(latest_mjai_msg["pai"])
                self.pai_unicode_art.update(TILE_2_UNICODE_ART_RICH[latest_mjai_msg["pai"]])
            else:
                self.akagi_pai.label = "None"
                self.pai_unicode_art.update(TILE_2_UNICODE_ART_RICH["?"])
            # Action
            self.tehai = tehai
            self.tsumohai = tsumohai
            if not self.syncing and ENABLEPLAYWRIGHT and AUTOPLAY:
                self.app.set_timer(0.15, self.autoplay)

    @on(Checkbox.Changed, "#checkbox_autoplay")
    def checkbox_autoplay_changed(self, event: Checkbox.Changed) -> None:
        global AUTOPLAY
        AUTOPLAY = event.value
        pass

    def lose_weight(self, mjai_msg):
        # 暂时只处理打牌降重，感谢 hhsuki提供的降重方案
        if mjai_msg["type"] == "dahai":
            # 分离选项和权重
            choices = []
            weights = []
            for data in mjai_msg["meta"]:
                if data[0] in TILES and data[1] >= 0.15:  # 只保留权重大于或等于 0.15 的选项
                    choices.append(data[0])
                    weights.append(data[1])
            # 进行加权随机选择
            if choices:
                pai = random.choices(choices, weights=weights, k=1)[0]
                if mjai_msg['pai'] != pai:
                    mjai_msg['substitution'] = f"{mjai_msg['pai']} -> {pai}"
                    mjai_msg['lose_weight'] = True
                else:
                    mjai_msg['lose_weight'] = False
                mjai_msg['pai'] = pai 
                logger.debug(f"lose weight: {mjai_msg}, tehai:{self.tehai} tsumohai:{self.tsumohai}")
        return mjai_msg
    
    def stop_dahai_verification(self) -> None:
        if self.dahai_verfication_job is not None:
            self.dahai_verfication_job.stop()
            self.dahai_verfication_job = None
        
    def autoplay(self) -> None:
        delay_time = self.action.action_delay(self.app.mjai_msg_dict[self.flow_id][-1], self.isOtherLiqi)
        logger.debug(f"Start AutoPlay After {delay_time}s...")
        self.action.mjai2action(self.app.mjai_msg_dict[self.flow_id][-1], self.tehai, self.tsumohai, delay_time)
        self.stop_dahai_verification()
        self.dahai_verfication_job = self.set_interval(2.5, self.redo_action)

    def redo_action(self) -> None:
        if self.flow_id in self.app.mjai_msg_dict:
            logger.debug(f"Redo Action: {self.app.mjai_msg_dict[self.flow_id][-1]}, tehai: {self.tehai}, tsumohai: {self.tsumohai}")
            self.action.mjai2action(self.app.mjai_msg_dict[self.flow_id][-1], self.tehai, self.tsumohai, 0.0)

    def action_quit(self) -> None:
        self.app.set_timer(2, self.app.update_flow.resume)
        self.update_log.stop()
        self.app.pop_screen()


class FlowDisplay(Static):

    def __init__(self, flow_id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.flow_id = flow_id

    def compose(self) -> ComposeResult:
        yield Button(f"Flow {self.flow_id}", id=f"flow_{self.flow_id}_btn", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(FlowScreen(self.flow_id))
        self.app.update_flow.pause()

class Akagi(App):
    CSS_PATH = "client.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.liqi: dict[str, Tool] = {}
        self.bridge: dict[str, MajsoulBridge] = {}
        self.active_flows = []
        self.gm_msg_dict  = dict() # flow.id -> List[gm_msg]
        self.mjai_msg_dict  = dict() # flow.id -> List[mjai_msg]
        if config.playwright.enable:
            global ENABLEPLAYWRIGHT, AUTOPLAY
            ENABLEPLAYWRIGHT = True
            AUTOPLAY = True

    def on_mount(self) -> None:
        self.update_flow = self.set_interval(1, self.refresh_flow)
        self.get_messages_flow = self.set_interval(0.05, self.get_messages)

    def refresh_flow(self) -> None:
        flows = get_activated_flows()
        for flow_id in self.active_flows:
            if flow_id not in flows:
                try:
                    self.query_one(f"#flow_{flow_id}").remove()
                except NoMatches:
                    pass
                self.active_flows.remove(flow_id)
                self.gm_msg_dict.pop(flow_id)
                self.mjai_msg_dict.pop(flow_id)
                self.liqi.pop(flow_id)
                self.bridge.pop(flow_id)
        for flow_id in flows:
            try:
                self.query_one("#FlowContainer")
            except NoMatches:
                continue
            try:
                self.query_one(f"#flow_{flow_id}")
            except NoMatches:
                self.query_one("#FlowContainer").mount(FlowDisplay(flow_id, id=f"flow_{flow_id}"))
                self.active_flows.append(flow_id)
                self.gm_msg_dict[flow_id] = []
                self.mjai_msg_dict[flow_id] = []
                self.liqi[flow_id] = Tool()
                self.bridge[flow_id] = MajsoulBridge()

    def get_messages(self):
        for flow_id in self.active_flows:
            gm_msg = get_messages(flow_id)
            if gm_msg is not None:
                parse_msg = {'id': gm_msg.id, 'type': gm_msg.type, 'method': gm_msg.method, 'data': gm_msg.data}
                if parse_msg is not None:
                    self.gm_msg_dict[flow_id].append(parse_msg)
                    if parse_msg['method'] == '.lq.FastTest.authGame' and parse_msg['type'] == MsgType.Req:
                        self.app.push_screen(FlowScreen(flow_id))
                        pass
                    mjai_msg = self.bridge[flow_id].input(parse_msg)
                    if mjai_msg is not None:
                        if self.bridge[flow_id].reach and mjai_msg["type"] == "dahai":
                            mjai_msg["type"] = "reach"
                            self.bridge[flow_id].reach = False
                        self.mjai_msg_dict[flow_id].append(mjai_msg)

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield ScrollableContainer(id="FlowContainer")
        yield Footer()

    def on_event(self, event: Event) -> Coroutine[Any, Any, None]:
        return super().on_event(event)

    @on(Checkbox.Changed, "#checkbox_autoplay")
    def checkbox_autoplay_changed(self, event: Checkbox.Changed) -> None:
        global AUTOPLAY
        AUTOPLAY = event.value
        pass

    @on(Checkbox.Changed, "#checkbox_autonext")
    def checkbox_autonext_changed(self, event: Checkbox.Changed) -> None:
        global AUTONEXT
        AUTONEXT = event.value
        pass

    def action_quit(self) -> None:
        self.update_flow.stop()
        self.get_messages_flow.stop()
        self.exit()