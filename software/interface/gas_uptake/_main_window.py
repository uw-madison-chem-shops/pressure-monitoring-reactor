import os
import re
import platformdirs
import tomli
import time
import datetime
import sys
import pathlib
import numpy as np
import pyqtgraph as pg
import qtypes
import yaqc
from functools import partial
from qtpy import QtCore, QtGui, QtWidgets
import yaqc_bluesky
from .__version__ import *
from ._persistant_state import PersistantState


__here__ = pathlib.Path(__file__).absolute().parent


with open(__here__ / "colors.txt", "r") as f:
    colors = [line.strip() for line in f]


# make persistant state if it doesn't exist
persistant_state_path = platformdirs.user_data_path("gas_uptake") / "state.toml"
persistant_state_path.parent.mkdir(parents=True, exist_ok=True)
persistant_state_path.touch(exist_ok=True)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app, config):
        super().__init__()
        self.app = app
        self.__version__ = __version__
        # title
        title = "Gas Uptake Reactor Control"
        title += " | version %s" % self.__version__
        title += " | Python %i.%i" % (sys.version_info[0], sys.version_info[1])
        self.setWindowTitle(title)
        # state
        self._state = PersistantState(persistant_state_path)
        for i in range(12):
            k = f"tare_pressure_{i}"
            if k not in self._state:
                self._state[k] = 0.0
        # yaq
        self.data = np.full((14, 10000), np.nan)
        self.recording = False
        self.temp_client = yaqc.Client(host=config["temp_client"]["host"], port=config["temp_client"]["port"])
        self.pressure_clients = dict()
        self.pressure_clients["current_sense_upper"] = yaqc.Client(host=config["current_sense_upper"]["host"],
                                                               port=config["current_sense_upper"]["port"])
        self.pressure_clients["current_sense_lower"] = yaqc.Client(host=config["current_sense_lower"]["host"],
                                                               port=config["current_sense_lower"]["port"])
        self.record_started = time.time()
        #
        self._begin_poll_loop()

    def _begin_poll_loop(self):
        self.poll_timer = QtCore.QTimer()
        self.poll_timer.start(1000)  # milliseconds
        self.poll_timer.timeout.connect(self.poll)

    def create_central_widget(self):
        splitter = QtWidgets.QSplitter()
        self.root_item = qtypes.Null(label="")
        self.tree_widget = qtypes.TreeWidget(self.root_item)
        splitter.addWidget(self.tree_widget)
        # recording
        recording_node = qtypes.Null(label="Data")
        self.record_button = qtypes.Button("Begin Recording")
        self.record_button.updated_connect(self._on_record)
        recording_node.append(self.record_button)
        self.file_path_node = qtypes.String(label="Filepath")
        recording_node.append(self.file_path_node)
        self.time_recorded_node = qtypes.String(label="Time Recorded")
        recording_node.append(self.time_recorded_node)
        self.root_item.append(recording_node)
        # temperature
        temp_node = qtypes.Null(label="Temperature")
        temp_node.append(qtypes.Float("Current Value", units="degC"))
        self.temp_setpoint = qtypes.Float("Setpoint", units="degC")
        self.temp_setpoint.updated_connect(self._on_temp_setpoint_updated)
        self.temp_setpoint.set_value(0.0)
        temp_node.append(self.temp_setpoint)
        temp_advanced_node = qtypes.Null(label="Advanced")
        temp_advanced_node.append(qtypes.Float("P"))
        temp_advanced_node.append(qtypes.Float("I"))
        temp_advanced_node.append(qtypes.Float("D"))
        temp_node.append(temp_advanced_node)
        self.root_item.append(temp_node)
        # pressure
        self.pressure_node = qtypes.Null(label="Pressure")
        for i in range(12):
            node = qtypes.Float(label=f"Transducer {i}", units="PSI")
            node.append(qtypes.Float("Offset", units="PSI", value=self._state[f"tare_pressure_{i}"], disabled=True))
            node.append(qtypes.Float("Tare Value", units="PSI", value=0.0))
            button = qtypes.Button(f"Tare Transducer {i} Now")
            button.updated_connect(self._on_tare)
            node.append(button)
            self.pressure_node.append(node)
        self.root_item.append(self.pressure_node)
        # graph
        self.graph = self._create_graph()
        splitter.addWidget(self.graph)
        # finish
        self.tree_widget[0].expand(depth=0)
        self.tree_widget[1].expand(depth=0)
        self.tree_widget[2].expand(depth=0)
        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
        splitter.setStretchFactor(0, 75)
        splitter.setStretchFactor(1, 50)
        self.setCentralWidget(splitter)

    def _create_data_file(self):
        now = datetime.datetime.now()
        fname = "gas-uptake_" + now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        data_directory = platformdirs.user_desktop_path() / "gas-uptake-data"
        fp = data_directory / fname
        tab = "\t"
        newline = "\n"
        with open(fp, "a") as f:
            f.write("timestamp:" + tab + "'" + now.isoformat() + "'" + newline)
            f.write("gas-uptake version:" + tab + "'" +  __version__ + "'" + newline)
            f.write("please cite yaq:" + tab + "https://doi.org/10.1063/5.0135255" + newline)
            f.write("please cite bluesky:" + tab + "https://doi.org/10.1080/08940886.2019.1608121" + newline)
            f.write("temperature units:" + tab + "'C'" + newline)
            f.write("pressure units:" + tab + "'PSI'" + newline)
            f.write("column:" + tab + "[")
            f.write("'labtime'")
            f.write(tab + "'temperature'")
            for i in range(12):
                f.write(tab + f"'pressure_{i}'")
            f.write("]" + newline)
        return fp

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

    def _on_record(self, value):
        self.recording = not self.recording
        if self.recording:
            # array
            self.data = np.full((14, 10000), np.nan)
            self.record_started = time.time()
            # init data file
            self.data_file_path = self._create_data_file()
            self.file_path_node.set_value(str(self.data_file_path))
            self.recording = True
            # button color
            #self.record_button.set_background("#c82829")
            #self.record_button.setText("STOP RECORDING")
        else:
            self.recording = False
            # button color
            self.record_button.set_background("#718c00")
            self.record_button.setText("BEGIN RECORDING")
        self.poll_timer.start(1000)

    def _on_temp_setpoint_updated(self, value):
        self.temp_client.set_position(value["value"])

    def _on_tare(self, value):
        print("on tare", value)
        transducer_index = int(re.findall(r'\d+(?:[.,]\d+)?', value["label"])[0])
        print("on tare", transducer_index)
        node = self.pressure_node[transducer_index]
        measured = node.get()["value"]
        measured -= self._state[f"tare_pressure_{transducer_index}"]
        actual = node[1].get()["value"]
        correction = actual - measured
        self._state[f"tare_pressure_{transducer_index}"] = correction

    def poll(self):
        t = time.time()
        row = np.full(14, np.nan)
        # time
        row[0] = time.time()
        # temperature
        row[1] = self.temp_client.get_position()
        QtWidgets.QApplication.exec()
        # pressure
        raw = dict()
        for k, v in self.pressure_clients.items():
            raw[k] = v.get_measured()
            QtWidgets.QApplication.exec()
        measured_pressures = dict()
        # this mapping makes little sense, but it's how it's wired
        # deal with it
        # ---Blaise 2024-02-13
        measured_pressures[0] = raw["current_sense_upper"]["channel6"]
        measured_pressures[1] = raw["current_sense_upper"]["channel5"]
        measured_pressures[2] = raw["current_sense_upper"]["channel4"]
        measured_pressures[3] = raw["current_sense_upper"]["channel3"]
        measured_pressures[4] = raw["current_sense_lower"]["channel1"]
        measured_pressures[5] = raw["current_sense_lower"]["channel0"]
        measured_pressures[6] = raw["current_sense_upper"]["channel0"]
        measured_pressures[7] = raw["current_sense_upper"]["channel1"]
        measured_pressures[8] = raw["current_sense_lower"]["channel5"]
        measured_pressures[9] = raw["current_sense_lower"]["channel4"]
        measured_pressures[10] = raw["current_sense_lower"]["channel3"]
        measured_pressures[11] = raw["current_sense_lower"]["channel2"]
        for k, v in measured_pressures.items():
            v *= 1000  # A to mA
            v -= 4
            v *= 150/20  # mA to PSI
            if v < 0:
                v = float("nan")
            else:
                v += self._state[f"tare_pressure_{k}"]
            row[k+2] = v
        # record
        if self.recording:
            with open(self.data_file_path, "a") as f:
                for n in row:
                    f.write("%8.6f" % n)
                    f.write("\t")
                f.write("\n")
                QtWidgets.QApplication.exec()
        # finish
        self.data = np.roll(self.data, shift=-1, axis=1)
        self.data[:, -1] = row
        self.update_plot()
        self.update_widgets(row)

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

    def update_widgets(self, row):
        self.root_item[1][0].set_value(row[1])
        if self.recording:
            self.time_recorded_node.set_value(str(time.time() - self.record_started))
        for i in range(12):
            self.root_item[2][i].set_value(row[i+2])
            self.root_item[2][i][0].set_value(self._state[f"tare_pressure_{i}"])

def main():
    """Initialize application and main window."""
    app = QtWidgets.QApplication(sys.argv)
    with open(platformdirs.user_config_path("gas-uptake") / "config.toml", "rb") as f:
        config = tomli.load(f)
    main_window = MainWindow(app, config=config)
    main_window.create_central_widget()
    main_window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
