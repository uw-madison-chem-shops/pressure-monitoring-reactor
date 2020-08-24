# importing pyside2 submodules here fixes an import problem
#   that I don't understand
#   --- Blaise 2019-10-12
from PySide2 import QtCore, QtWidgets, QtGui

import appdirs
import os
import shutil

from ._main_window import main as begin


__here__ = os.path.abspath(os.path.dirname(__file__))
__base__ = os.path.dirname(os.path.dirname(__here__))


def main():
    """Start yaq application."""
    # create app data directory
    d = os.path.join(appdirs.user_data_dir(), "gas-uptake")
    if not os.path.isdir(d):
        os.mkdir(d)
    # begin
    begin()


if __name__ == "__main__":
    main()
