import asyncio
import time
import threading

from . import pRoot, conf, resver, init
from pathlib import Path
from playwright.sync_api import sync_playwright
from mhm.action import get_click_list, get_autohu
from mhm.akagi import Akagi, game_end_msgs
from loguru import logger

PROXINJECTOR = pRoot / "common/proxinject/proxinjector-cli"

AUTO_GAME = {
    "endGameStage": [
        (14.35, 8.12),    # 点击确定按钮，此坐标位于大厅的"商家"和"寻觅"按钮之间
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
        # 处理游戏结束消息
        if len(game_end_msgs) > 0:
            parse_msg = game_end_msgs.pop(0)
            if parse_msg['method'] == '.lq.NotifyGameEndResult':
                # 1.等待结算
                time.sleep(30)

                # 2.最终顺位界面点击"确认"
                xy_scale = {"x": AUTO_GAME['endGameStage'][0][0] * scale,
                            "y": AUTO_GAME['endGameStage'][0][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(1)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                time.sleep(5)

                # 3. 段位pt结算界面点击"确认"
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                time.sleep(10)

                # 4. 开启宝匣礼物
                xy_scale = {"x": AUTO_GAME['endGameStage'][1][0] * scale,
                            "y": AUTO_GAME['endGameStage'][1][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(1)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                time.sleep(5)

                # 5. 宝匣好感度界面点击"确认"
                xy_scale = {"x": AUTO_GAME['endGameStage'][0][0] * scale,
                            "y": AUTO_GAME['endGameStage'][0][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(1)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                time.sleep(5)

                # 6. 每日任务界面点击"确认"
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                time.sleep(8)

                # 7. 大厅界面点击段位场
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
        # start playweight thread
        if conf.playwright["enable"]:
            playwright_thread = threading.Thread(target=start_playwright)
            playwright_thread.daemon = True
            playwright_thread.start()

        # start texual terminal
        app = Akagi()
        app.run()
    except KeyboardInterrupt:
        exit(0)