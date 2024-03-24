import asyncio

from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster

from .addons import WebSocketAddon
from .config import config
from .hook import Hook


def _cmd(dikt):
    return [obj for key, value in dikt.items() for obj in (f"--{key}", value)]


async def start_proxy(hooks: list[Hook]):
    master = DumpMaster(Options(**config.mitmdump.args), **config.mitmdump.dump)
    master.addons.add(WebSocketAddon(hooks))
    await master.run()
    return master


async def start_inject():
    cmd = [config.proxinject.path, *_cmd(config.proxinject.args)]
    while True:
        process = await asyncio.subprocess.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()
        await asyncio.sleep(0.8)