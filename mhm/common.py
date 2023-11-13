import asyncio

from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options

from . import ROOT, logger, conf
from .addons import addons


def _cmd(dict):
    return [obj for key, value in dict.items() for obj in (f"--{key}", value)]


async def start_proxy():
    master = DumpMaster(
        Options(**conf["mitmdump"]),
        **conf["dump"],
    )

    master.addons.add(*addons)
    await master.run()
    return master


async def start_inject():
    cmd = [
        ROOT / "common/proxinject/proxinjector-cli",
        *_cmd(conf["proxinject"]),
    ]

    process = await asyncio.subprocess.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    await asyncio.sleep(0.8)
    asyncio.create_task(start_inject())


def main():
    try:
        loop = asyncio.get_event_loop()

        logger.info(f"[i]log level: {conf['mhm']['log_level']}")
        logger.info(f"[i]pure python protobuf: {conf['mhm']['pure_python_protobuf']}")

        if "server" in conf:
            logger.info(f"[i]version: {conf['server']['version']}")
            logger.info(f"[i]max_charid: {conf['server']['max_charid']}")

        if "mitmdump" in conf:
            loop.create_task(start_proxy())
            logger.info(f"[i]mitmdump launched @ {len(conf['mitmdump']['mode'])} mode")

        if conf.get("proxinject", None):
            loop.create_task(start_inject())
            logger.info(f"[i]proxinject launched @ {conf['proxinject']['set-proxy']}")

        loop.run_forever()
    except KeyboardInterrupt:
        pass
