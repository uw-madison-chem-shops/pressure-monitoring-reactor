__all__ = ["GasUptakeDirector"]

import os
import asyncio
from typing import Dict, Any
import datetime
import numpy as np
import tidy_headers

from yaqd_core import Base, logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

os.chdir(os.path.expanduser("~"))
data_directory = pathlib.Path("Desktop/gas-uptake-data")


def write_row(path, row):
    with open(self.record_path, "ab") as f:
        np.savetxt(f, row, fmt="%8.6f", delimiter="\t", newline="\t")
        f.write(b"\n")


class GasUptakeDirector(Base):
    _kind = "gas-uptake-director"
    defaults: Dict[str, Any] = {}

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self.recording = False
        self.temps = np.full(100, np.nan)

    def begin_recording(self):
        # create file
        now = datetime.datetime.now()
        fname = "gas-uptake_" + now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        self.record_path = data_directory / fname
        headers = {}
        headers["timestamp"] = now.isoformat()
        headers["gas-uptake version"] = __version__
        headers["temperature units"] = "C"
        headers["pressure units"] = "PSI"
        cs = []
        cs.append("labtime")
        cs.append("temperature")
        for i in range(12):
            cs.append(f"pressure_{i}")
        headers["column"] = cs
        tidy_headers.write(self.record_path, headers)
        # finish
        self.recording = True
        return self.record_path

    def stop_recording(self):
        self.recording = False

    def set_temperature(self, temp):
        self.set_temperature = temp

    def poll(self):
        row = [time.time()]
        # temperature
        m = self._temp_client.get_measured()
        self._temp_client.measure()
        value = m["temperature"]
        self.temp_table["current"].write(value, units="deg_C")
        row.append(value)
        # pressure
        measured = []
        for client in [
            self._pressure_client_a,
            self._pressure_client_b,
            self._pressure_client_c,
        ]:
            m = client.get_measured()
            for channel in range(4):
                value = m[f"channel_{channel}"]
                value -= 4
                value *= 150 / 20  # mA to PSI
                if value < 0:
                    value = np.nan
                measured.append(value)
                self.pressure_table[f"sensor_{len(measured)-1}"].write(value)
                row.append(value)
            client.measure()
        # append to data
        self.temps = np.roll(self.temps, shift=-1)
        self.temps[-1] = row[1]
        # write to file
        if self.recording:
            write_row(path, row)
        # PID
        p = 0.25 * (self.temps - self.set_temperature)
        i = 0.2 * np.sum(self.temps - self_temperature) / 100
        d = 0.001 * 0
        duty = p + i + d
        print("duty", p, i, d, duty)
        if np.isnan(duty):
            self._heater_client.set_value(0)
        elif duty < -1:
            self._heater_client.set_value(1)
        elif duty > 0:
            self._heater_client.set_value(0)
        else:
            on = -duty
            off = 1 + duty
            self._heater_client.blink(on, off)
