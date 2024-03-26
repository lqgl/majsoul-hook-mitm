import time, random

from .config import config
from playwright.sync_api import sync_playwright
from pathlib import Path
from .akagi import get_game_msgs, get_auto_next
from .action import get_click_list, get_autohu
from loguru import logger

LOCATION = {
    "endGameStage": [
        (14.35, 8.12),      # 点击确定按钮，此坐标位于大厅的"商家"和"寻觅"按钮之间
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
    "emotions": [
        (12.4, 3.5), (13.65, 3.5), (14.8, 3.5),    # 1 2 3
        (12.4, 5.0), (13.65, 5.0), (14.8, 5.0),    # 4 5 6
        (12.4, 6.5), (13.65, 6.5), (14.8, 6.5),    # 7 8 9
    ]
}

def randomEmotion(page, scale, parse_msg):
    if parse_msg['method'] == '.lq.NotifyGameBroadcast':
        randomN = random.uniform(0.0, 100.0)
        # 50%
        if randomN <= 50.0:
            xy = (15.675, 4.9625)
            xy_scale = {"x":xy[0]*scale,"y":xy[1]*scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.1)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker: {xy_scale} click emotions")
            time.sleep(0.3)
            # index = random.randint(0, 8)
            index = 2
            xy = LOCATION["emotions"][index]
            xy_scale = {"x":xy[0]*scale,"y":xy[1]*scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.1)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker: {xy_scale} click the {index} emotion")

def auto_next(page, scale, parse_msg):
    if parse_msg['method'] == '.lq.NotifyGameEndResult':
        # 1.等待结算
        time.sleep(30)

        # 2.最终顺位界面点击"确认"
        xy_scale = {"x": LOCATION['endGameStage'][0][0] * scale,
                    "y": LOCATION['endGameStage'][0][1] * scale}
        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
        time.sleep(1)
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        time.sleep(5)

        # 3. 段位pt结算界面点击"确认"
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        time.sleep(10)

        # 4. 开启宝匣礼物
        xy_scale = {"x": LOCATION['endGameStage'][1][0] * scale,
                    "y": LOCATION['endGameStage'][1][1] * scale}
        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
        time.sleep(1)
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        time.sleep(5)

        # 5. 宝匣好感度界面点击"确认"
        xy_scale = {"x": LOCATION['endGameStage'][0][0] * scale,
                    "y": LOCATION['endGameStage'][0][1] * scale}
        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
        time.sleep(1)
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        time.sleep(5)

        # 6. 每日任务界面点击"确认"
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        time.sleep(8)

        # 7. 大厅界面点击段位场
        xy_scale = {"x": LOCATION['endGameStage'][2][0] * scale,
                    "y": LOCATION['endGameStage'][2][1] * scale}
        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
        time.sleep(0.5)
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        logger.debug(f"page_clicker_next_game: {xy_scale}")
        time.sleep(2)
    elif parse_msg['method'] == '.lq.NotifyGameTerminate':
        time.sleep(8)
        xy_scale = {"x": LOCATION['endGameStage'][2][0] * scale,
                    "y": LOCATION['endGameStage'][2][1] * scale}
        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
        time.sleep(0.5)
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        logger.debug(f"page_clicker_next_game: {xy_scale}")
        time.sleep(2)

    if parse_msg['method'] == '.lq.NotifyGameEndResult' or parse_msg[
        'method'] == '.lq.NotifyGameTerminate':
        if config.playwright.auto_next_args.get('next_game_Rank') == 'gold':
            xy_scale = {"x": LOCATION['rankStage'][0][0] * scale,
                        "y": LOCATION['rankStage'][0][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker_next_game_gold: {xy_scale}")
            time.sleep(2)
        elif config.playwright.auto_next_args.get('next_game_Rank') == 'silver':
            xy_scale = {"x": LOCATION['rankStage'][1][0] * scale,
                        "y": LOCATION['rankStage'][1][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker_next_game_silver: {xy_scale}")
            time.sleep(2)
        elif config.playwright.auto_next_args.get('next_game_Rank') == 'copper':
            xy_scale = {"x": LOCATION['rankStage'][2][0] * scale,
                        "y": LOCATION['rankStage'][2][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker_next_game_copper: {xy_scale}")
            time.sleep(2)
        elif config.playwright.auto_next_args.get('next_game_Rank') == 'jade':
            xy_scale = {"x": LOCATION['rankStage'][0][0] * scale,
                        "y": LOCATION['rankStage'][0][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.wheel(0, 100)
            page.mouse.wheel(0, 100)
            page.mouse.wheel(0, 100)
            page.mouse.wheel(0, 100)
            time.sleep(2)
            xy_scale = {"x": LOCATION['rankStage'][3][0] * scale,
                        "y": LOCATION['rankStage'][3][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker_next_game_jade: {xy_scale}")
            time.sleep(2)
        elif config.playwright.auto_next_args.get('next_game_Rank') == 'king':
            xy_scale = {"x": LOCATION['rankStage'][0][0] * scale,
                        "y": LOCATION['rankStage'][0][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.wheel(0, 100)
            page.mouse.wheel(0, 100)
            page.mouse.wheel(0, 100)
            page.mouse.wheel(0, 100)
            time.sleep(2)
            xy_scale = {"x": LOCATION['rankStage'][4][0] * scale,
                        "y": LOCATION['rankStage'][4][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker_next_game_king: {xy_scale}")
            time.sleep(2)

        if config.playwright.auto_next_args.get('next_game_number') == '4p':
            if config.playwright.auto_next_args.get('next_game_rounds') == 'south':
                xy_scale = {"x": LOCATION['roomsAndRoundsStage'][0][0] * scale,
                            "y": LOCATION['roomsAndRoundsStage'][0][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_4p_south: {xy_scale}")
                time.sleep(1)
            elif config.playwright.auto_next_args.get('next_game_rounds') == 'east':
                xy_scale = {"x": LOCATION['roomsAndRoundsStage'][1][0] * scale,
                            "y": LOCATION['roomsAndRoundsStage'][1][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_4p_east: {xy_scale}")
                time.sleep(1)
        elif config.playwright.auto_next_args.get('next_game_number') == '3p':
            if config.playwright.auto_next_args.get('next_game_rounds') == 'south':
                xy_scale = {"x": LOCATION['rankStage'][2][0] * scale,
                            "y": LOCATION['rankStage'][2][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                time.sleep(2)
                xy_scale = {"x": LOCATION['roomsAndRoundsStage'][3][0] * scale,
                            "y": LOCATION['roomsAndRoundsStage'][3][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_3p_south: {xy_scale}")
                time.sleep(1)
            elif config.playwright.auto_next_args.get('next_game_rounds') == 'east':
                xy_scale = {"x": LOCATION['rankStage'][2][0] * scale,
                            "y": LOCATION['rankStage'][2][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                time.sleep(2)
                xy_scale = {"x": LOCATION['roomsAndRoundsStage'][4][0] * scale,
                            "y": LOCATION['roomsAndRoundsStage'][4][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_3p_east: {xy_scale}")
                time.sleep(1)
        
def start_playwright():
    playwright_width = config.playwright.args.get("width")
    playwright_height = config.playwright.args.get("height")
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
        game_msgs = get_game_msgs()
        if len(game_msgs) > 0:
            parse_msg = game_msgs.pop(0)
            if config.playwright.auto_emotion:
                randomEmotion(page, scale, parse_msg)
            elif get_auto_next():
                auto_next(page, scale, parse_msg)
        click_list = get_click_list()
        if len(click_list) > 0:
            xy = click_list.pop(0)
            xy_scale = {"x":xy[0]*scale,"y":xy[1]*scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.1)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker: {xy_scale}")
            do_autohu = get_autohu()
            if do_autohu:
                # logger.debug(f"do_autohu")
                page.evaluate("() => view.DesktopMgr.Inst.setAutoHule(true)")
                # page.locator("#layaCanvas").click(position=xy_scale)
                do_autohu = False
        else:
            time.sleep(1)  # thread will block here