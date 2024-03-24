import os

from google.protobuf import __version__
from rich.console import Console

if __version__.split(".") > ["3", "18", "0"]:
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

console = Console()