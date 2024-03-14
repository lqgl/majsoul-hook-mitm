import asyncio
import time
import threading

from . import pRoot, logger, conf, resver, init
from pathlib import Path
from mitmproxy import ctx
from playwright.sync_api import sync_playwright

from mhm.action import Action
from mhm.majsoul2mjai import MajsoulBridge
from mhm.action import get_click_list, get_autohu
from mhm.addons import get_messages

PROXINJECTOR = pRoot / "common/proxinject/proxinjector-cli"

AUTO_GAME = {
    "endGameStage": [
        (14.75, 8.3375),
        (6.825, 6.8),
        (11.5, 2.75),
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

    init()
    try:
        # Create and start the proxy server thread
        proxy_thread = threading.Thread(target=lambda: asyncio.run(start()))
        proxy_thread.start()

        if conf.playwright['enable']:
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

            action = Action()
            bridge = MajsoulBridge()

            while True:
                gm_msgs = get_messages()
                if len(gm_msgs) > 0: 
                    gm_msg = gm_msgs.pop(0)
                    parse_msg = {'id': gm_msg.id, 'type': gm_msg.type, 'method': gm_msg.method, 'data': gm_msg.data}

                    if conf.autoNextGame.enable_auto_next_game:
                        if parse_msg['method'] == '.lq.NotifyGameEndResult':
                            time.sleep(20)
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

                    if gm_msg.method == '.lq.ActionPrototype':
                        if 'operation' in gm_msg.data.get('data'):
                            if 'operation_list' in gm_msg.data.get('data').get('operation'):
                                action.latest_operation_list = gm_msg.data.get('data').get('operation').get('operation_list') 
                        if gm_msg.data.get('name') == 'ActionDiscardTile':
                            action.isNewRound = False
                        if gm_msg.data.get('name') == 'ActionNewRound':
                            action.isNewRound = True
                            action.reached = False     
                    mjai_msg = bridge.input(parse_msg)    
                    if mjai_msg is not None:
                        # 处理 mjai_msg，如果 reach 为真，则将 type 改为 "reach"
                        if bridge.reach and mjai_msg["type"] == "dahai":
                            mjai_msg["type"] = "reach"
                            bridge.reach = False
                        print('-'*65)
                        print(mjai_msg)
                        action.mjai2action(mjai_msg, bridge.my_tehais, bridge.my_tsumohai)
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
                    time.sleep(1)  # main thread will block here
    except KeyboardInterrupt:
        playwrightContextManager.__exit__()
        ctx.master.shutdown()
        exit(0)
