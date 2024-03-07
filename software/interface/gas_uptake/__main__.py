import click
import platformdirs
import sys
import subprocess
import os
import tomli

from ._main_window import main as begin
from .__version__ import __version__


@click.group()
@click.version_option(__version__)
def main():
    pass


@main.command(name="edit-config")
def edit_config():
    path = platformdirs.user_config_path("gas-uptake") / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)

    while True:
        if sys.platform.startswith("win32"):
            subprocess.run([os.environ.get("EDITOR", "notepad.exe"), str(path)])
        else:
            subprocess.run([os.environ.get("EDITOR", "vi"), path])
        try:
            with open(path, "rb") as f:
                tomli.load(f)
            break
        except Exception as e:
            print(e, file=sys.stderr)

            if not click.confirm(
                "Error parsing config toml. Would you like to re-edit?",
                default=True,
            ):
                break


@main.command(name="run")
def _run():
    # create app data directory
    d = os.path.join(platformdirs.user_data_dir(), "gas-uptake")
    if not os.path.isdir(d):
        os.mkdir(d)
    # begin
    begin()
