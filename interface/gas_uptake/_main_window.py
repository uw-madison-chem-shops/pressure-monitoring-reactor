import appdirs
import ctypes
import logging
import os
import sys

import WrightTools as wt
import qtypes

import PySide2
from PySide2 import QtCore, QtGui, QtWidgets

from .__version__ import *

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
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("gas-uptake")
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
        layout = QtWidgets.QHBoxLayout()
        # status widget ---------------------------------------------------------------------------
        self.status_widget = QtWidgets.QWidget()
        self.status_widget.setLayout(QtWidgets.QVBoxLayout())
        self.status_widget.layout().setContentsMargins(0, 0, 0, 0)
        # status_scroll_area
        self.status_scroll_area = qtypes.widgets.ScrollArea()
        self.status_widget.layout().addWidget(self.status_scroll_area, 0)
        # temp
        self.temp_table = qtypes.widgets.InputTable()
        self.temp_table.append(None, "temperature")
        self.current_temp = qtypes.Number(disabled=True)
        self.set_temp = qtypes.Number(initial_value=200)
        self.temp_table.append(
            qtypes.Number(name="current", disabled=True, units="deg_C")
        )
        self.temp_table.append(qtypes.Number(name="set", units="deg_C"))
        self.temp_table.append(qtypes.Number(name="test"))
        print(self.temp_table.keys())

        self.status_scroll_area.add_widget(self.temp_table)
        self.set_temperature = qtypes.widgets.PushButton("SET TEMPERATURE")
        self.status_scroll_area.add_widget(self.set_temperature)
        # pressure
        self.pressure_table = qtypes.widgets.InputTable()
        # self.pressure_table.append("PRESSURE", None)
        self.current_pressures = []
        for i in range(12):
            n = qtypes.Number(disabled=True)
            # self.current_pressures.append(n)
            # self.pressure_table.append(f"SENSOR {i}", n)
        self.status_scroll_area.add_widget(self.pressure_table)
        #
        layout.addWidget(self.status_widget, 0)
        # main widget -----------------------------------------------------------------------------
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(QtWidgets.QVBoxLayout())
        main_widget.layout().setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget, 1)
        # progress bar
        self.progress_bar = qtypes.widgets.ProgressBar()
        self.progress_bar.setValue(50)
        main_widget.layout().addWidget(self.progress_bar)
        # hboxlayout
        hbox_widget = QtWidgets.QWidget()
        hbox_widget.setLayout(QtWidgets.QHBoxLayout())
        hbox_widget.layout().setContentsMargins(0, 0, 0, 0)
        main_widget.layout().addWidget(hbox_widget)
        # graph
        self.graph = qtypes.widgets.Graph()
        hbox_widget.layout().addWidget(self.graph)
        # measure scroll area
        self.record_scroll_area = qtypes.widgets.ScrollArea()
        hbox_widget.layout().addWidget(self.record_scroll_area)
        # record
        self.record_table = qtypes.widgets.InputTable()
        # self.record_table.append("RECORD", None)
        self.record_scroll_area.add_widget(self.record_table)
        self.record_button = qtypes.widgets.PushButton("BEGIN RECORDING")
        self.record_scroll_area.add_widget(self.record_button)
        # display
        self.display_table = qtypes.widgets.InputTable()
        # self.display_table.append("DISPLAY", None)
        self.plot_temperature = qtypes.Bool(True)
        # self.display_table.append("SHOW TEMPERATURE", self.plot_temperature)
        self.plot_pressures = []
        for i in range(12):
            b = qtypes.Bool(True)
            # self.plot_pressures.append(b)
            # self.display_table.append(f"SHOW PRESSURE {i}", b)
        self.record_scroll_area.add_widget(self.display_table)
        self.tare_pressure_button = qtypes.widgets.PushButton("TARE PRESSURES")
        self.record_scroll_area.add_widget(self.tare_pressure_button)
        # finish
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)


# --- main ----------------------------------------------------------------------------------------


def main():
    """Initialize application and main window."""
    app = QtWidgets.QApplication(["yaq"])
    main_window = MainWindow(app)
    main_window.create_central_widget()
    main_window.showMaximized()
    app.exec_()


if __name__ == "__main__":
    main()
