import asyncio, threading, time

from mhm import console
from mhm.common import start_inject, start_proxy
from mhm.config import config, load_resource
from mhm.hook import Hook
from mhm.resource import ResourceManager
from mhm.akagi import Akagi
from mhm.playwright import start_playwright
from loguru import logger


def create_hooks(resger: ResourceManager) -> list[Hook]:
    hooks = []
    if config.base.aider:
        from mhm.hook.aider import DerHook

        hooks.append(DerHook())
    if config.base.chest:
        from mhm.hook.chest import EstHook

        hooks.append(EstHook(resger))
    if config.base.skins:
        from mhm.hook.skins import KinHook

        hooks.append(KinHook(resger))
    return hooks


def main():
    # 日志设定
    logger.remove(handler_id=None)
    logger.add("mhm.log", level = "DEBUG")
    logger.info(f"Debug: {config.base.debug}")
    logger.info("Load Resource")
    with console.status("[magenta]Fetch LQC.LQBIN"):
        resger = load_resource(config.base.no_cheering_emotes)
    console.log(f"LQBin Version: [cyan3]{resger.version}")
    logger.info(f"> {len(resger.item_rows):0>3} items")
    logger.info(f"> {len(resger.title_rows):0>3} titles")
    logger.info(f"> {len(resger.character_rows):0>3} characters")

    logger.info("Init Hooks")
    hooks = create_hooks(resger)
    for h in hooks:
        logger.info(f"> [cyan3]{h.__class__.__name__}")

    async def start():
        tasks = set()
        if config.mitmdump.args:
            tasks.add(start_proxy(hooks))
            logger.info(f"Start mitmdump @ {config.mitmdump.args.get('mode')}")
        if config.proxinject.enable:
            tasks.add(start_inject())
            logger.info(f"Start proxinject @ {config.proxinject.args.get('set-proxy')}")
        await asyncio.gather(*tasks)

    try:
        # Create and start the proxy server thread
        proxy_thread = threading.Thread(target=lambda: asyncio.run(start()))
        proxy_thread.daemon = True
        proxy_thread.start()
        # wait for mitmproxy start
        time.sleep(1)
        # start playweight thread
        if config.playwright.enable:
            playwright_thread = threading.Thread(target=start_playwright)
            playwright_thread.daemon = True
            playwright_thread.start()
        # start texual terminal
        app = Akagi()
        app.run()
    except KeyboardInterrupt:
        exit(0)

if __name__ == "__main__":
    main()