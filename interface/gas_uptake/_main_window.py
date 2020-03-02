import os
import time
import datetime
import sys
import pathlib
import numpy as np
import pyqtgraph as pg
import qtypes
import PyQt5
import yaqc
from PyQt5 import QtCore, QtGui, QtWidgets
from .__version__ import *


__here__ = pathlib.Path(__file__).absolute().parent

os.chdir(os.path.expanduser("~"))
data_directory = pathlib.Path("Desktop/gas-uptake-data")

if not os.path.isdir(data_directory):
    os.mkdir(data_directory)


with open(__here__ / "colors.txt", "r") as f:
    colors = [line.strip() for line in f]
    print(colors)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        # self.start_time = wt.kit.TimeStamp()
        self.app = app
        self.__version__ = __version__
        # title
        title = "Gas Uptake Reactor Control"
        title += " | version %s" % self.__version__
        title += " | Python %i.%i" % (sys.version_info[0], sys.version_info[1])
        self.setWindowTitle(title)
        #
        self.data = np.full((14, 10000), np.nan)
        self.recording = False
        self.client = yaqc.Client(39000)
        self.record_started = 0

    def _begin_poll_loop(self):
        self.poll_timer = QtCore.QTimer()
        self.poll_timer.start(1000)  # milliseconds
        self.poll_timer.timeout.connect(self.poll)

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
        # record
        self.record_button = qtypes.widgets.PushButton(
            "BEGIN RECORDING", background="#718c00"
        )
        self.record_button.clicked.connect(self._on_record)
        self.status_scroll_area.add_widget(self.record_button)
        # temp
        self.temp_table = qtypes.widgets.InputTable()
        self.temp_table.append(None, "temperature")
        self.temp_table.append(qtypes.Number(name="current", disabled=True))
        n = qtypes.Number(name="set")
        n.limits.write(-100, 170)
        self.temp_table.append(n)
        self.status_scroll_area.add_widget(self.temp_table)
        # pressure
        self.pressure_table = qtypes.widgets.InputTable()
        self.pressure_table.append(None, label="pressure")
        for i in range(12):
            self.pressure_table.append(qtypes.Number(disabled=True, name=f"sensor_{i}"))
        self.status_scroll_area.add_widget(self.pressure_table)
        #
        layout.addWidget(self.status_widget, 0)
        # main widget -----------------------------------------------------------------------------
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(QtWidgets.QVBoxLayout())
        main_widget.layout().setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget, 1)
        # hboxlayout
        hbox_widget = QtWidgets.QWidget()
        hbox_widget.setLayout(QtWidgets.QHBoxLayout())
        hbox_widget.layout().setContentsMargins(0, 0, 0, 0)
        main_widget.layout().addWidget(hbox_widget)
        # graph
        self.graph = self._create_graph()
        hbox_widget.layout().addWidget(self.graph)
        # finish
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def _create_graph(self):
        pw = pg.PlotWidget()
        pw.addLegend(offset=(5, -5))
        #
        self.graph_curves = {}
        self.graph_curves["temperature"] = pg.PlotCurveItem(name="temp.")
        for i in range(12):
            c = colors[i]
            self.graph_curves[f"pressure_{i}"] = pg.PlotCurveItem(name=i, pen=(c))
        #
        self.p1 = pw.plotItem
        self.p1.setLabels(right="temperature (C)", bottom="time (min)")
        self.p1.addItem(self.graph_curves["temperature"])
        self.p1.setYRange(0, 300)
        #
        self.p2 = pg.ViewBox()
        self.p1.showAxis("right")
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis("left").linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis("left").setLabel("absolute pressure (PSI)")
        for i in range(12):
            key = f"pressure_{i}"
            self.p2.addItem(self.graph_curves[key])
            self.p1.legend.addItem(self.graph_curves[key], i)
        #
        return pw

    def _on_record(self):
        self.recording = not self.recording
        if self.recording:
            self.client.begin_recording()
            # button color
            self.record_button.set_background("#c82829")
            self.record_button.setText("STOP RECORDING")
            # array
            self.data = np.full((14, 10000), np.nan)
            self.record_started = time.mktime(now.timetuple())
        else:
            self.client.stop_recording()
            # button color
            self.record_button.set_background("#718c00")
            self.record_button.setText("BEGIN RECORDING")
        self.poll_timer.start(1000)

    def poll(self):
        self.data = np.roll(self.data, shift=-1, axis=1)
        self.data[:, -1] = self.client.get_last_reading()

    def set_temperature(self, value, units):
        print("set temperature", value, units)

    def tare_pressures(self):
        print("tare pressures")

    def update_plot(self):
        xi = self.data[0] - self.record_started
        xi /= 60
        self.graph_curves["temperature"].setData(x=xi, y=self.data[1])
        for i in range(12):
            self.graph_curves[f"pressure_{i}"].setData(x=xi, y=self.data[i + 2])
        #
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
        self.p2.setYRange(0, np.nanmax(self.data[2:]))


def main():
    """Initialize application and main window."""
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(app)
    main_window.create_central_widget()
    main_window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
