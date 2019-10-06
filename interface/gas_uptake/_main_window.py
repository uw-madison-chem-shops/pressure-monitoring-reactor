import appdirs
import ctypes
import logging
import os
import sys

import WrightTools as wt

import PySide2
from PySide2 import QtCore, QtGui, QtWidgets

from .__version__ import *

# from ..core.ini import INI
# from .progress_bar import ProgressBar
# from .push_button import PushButton
# from .settings_widget import SettingsWidget
# from .scroll_area import ScrollArea
# from .tab_widget import TabWidget
# from .yaq_widget import YAQWidget


here = os.path.abspath(os.path.dirname(__file__))

# colors = INI(os.path.join(here, "colors.ini")).dictionary["night"]

log = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.start_time = wt.kit.TimeStamp()
        self.app = app
        self.__version__ = __version__
        # title
        title = "Gas Uptake Reactor Control"
        title += " | version %s" % self.__version__
        title += " | Python %i.%i" % (sys.version_info[0], sys.version_info[1])
        self.setWindowTitle(title)
        # style sheet
        # style_sheet = "QWidget{background-color: %s}" % colors["background"]
        # self.setStyleSheet(style_sheet)
        # disable 'x'
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
        # platform specific
        if os.name == "posix":
            pass
        elif os.name == "nt":
            # must have unique app ID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("yaq")
            # icon

    def center(self):
        """Center the window within the current screen."""
        raise NotImplementedError
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2
        )

    def create_central_widget(self):
        self.central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        """
        # scroll area
        self.scroll_area = ScrollArea()
        #
        settings_button = PushButton("SETTINGS", "yellow")
        settings_button.clicked.connect(self.show_settings)
        self.scroll_area.add_widget(settings_button)
        #
        shutdown_button = PushButton("SHUTDOWN", "red")
        shutdown_button.clicked.connect(self.on_shutdown_clicked)
        self.scroll_area.add_widget(shutdown_button)
        #
        layout.addWidget(self.scroll_area, 0, 0)
        # main area
        self.container_widget = QtWidgets.QWidget()
        self.container_widget.setLayout(QtWidgets.QHBoxLayout())
        self.container_widget.layout().setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container_widget, 0, 1)
        # finish
        """
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def create_settings_widget(self):
        self.settings_widget = SettingsWidget(self)
        self.container_widget.layout().addWidget(self.settings_widget)
        self.settings_widget.hide()

    def initialize_hardware(self):
        # TODO: this is temporary
        # eventually this should be moved under settings I think (?)
        # so that it can be properly dynamic...
        from ..hardware.hardware import Hardware
        from ..hardware.Rodeostat.driver import Driver
        from ..hardware.GUI import GUI

        hw = Hardware(self, Driver, {}, GUI, "test", "rodeo")

    def initialize_log(self):
        d = os.path.join(appdirs.user_data_dir(), "pytentiostat", "logs")
        if not os.path.isdir(d):
            os.mkdir(d)
        p = os.path.join(d, self.start_time.path + ".log")
        elements = [
            "%(asctime)s",
            "%(levelname)s",
            "%(name)s",
            "%(funcName)s",
            "%(message)s",
        ]
        fmt = "|".join(elements)
        logging.basicConfig(filename=p, level=logging.DEBUG, format=fmt)
        logging.captureWarnings(True)
        log.info("log initialized")

    def on_shutdown_clicked(self):
        print("on shutdown clicked")
        log.info("attempting shutdown")
        self.close()

    def show_settings(self):
        self.settings_widget.show()


# --- main ----------------------------------------------------------------------------------------


def main():
    """Initialize application and main window."""
    app = QtWidgets.QApplication(["yaq"])
    main_window = MainWindow(app)
    main_window.initialize_log()
    # main_window.create_central_widget()
    # main_window.create_settings_widget()
    # main_window.initialize_hardware()
    main_window.showMaximized()
    app.exec_()


if __name__ == "__main__":
    main()
