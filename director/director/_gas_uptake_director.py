__all__ = ["GasUptakeDirector"]

import os
import time
import yaqc
import asyncio
from typing import Dict, Any
import datetime
import collections
import pathlib

from yaqd_core import Base, logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

os.chdir(os.path.expanduser("~"))
data_directory = pathlib.Path("Desktop/gas-uptake-data")


def write_row(path, row):
    with open(self.record_path, "ab") as f:
        for n in row:
            f.write(b"%8.6f" % n)
        f.write(b"\n")


class GasUptakeDirector(Base):
    _kind = "gas-uptake-director"
    defaults: Dict[str, Any] = {}

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self.recording = False
        self.temps = collections.deque(maxlen=100)
        self.set_temp = 0
        # initialize clients
        self._heater_client = yaqc.Client(38455)
        self._heater_client.set_value(0)
        self._temp_client = yaqc.Client(39001)
        self._temp_client.measure()
        self._pressure_client_a = yaqc.Client(39100)
        self._pressure_client_a.set_state(gain=2, size=16)
        self._pressure_client_a.measure()
        self._pressure_client_b = yaqc.Client(39101)
        self._pressure_client_b.set_state(gain=2, size=16)
        self._pressure_client_b.measure()
        self._pressure_client_c = yaqc.Client(39102)
        self._pressure_client_c.set_state(gain=2, size=16)
        self._pressure_client_c.measure()
        # begin looping
        self._loop.create_task(self._runner())

    def begin_recording(self):
        # create file
        now = datetime.datetime.now()
        fname = "gas-uptake_" + now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        self.record_path = data_directory / fname
        headers = {}
        headers["timestamp"] = now.isoformat()
        #headers["gas-uptake version"] = __version__
        headers["temperature units"] = "C"
        headers["pressure units"] = "PSI"
        cs = []
        cs.append("labtime")
        cs.append("temperature")
        for i in range(12):
            cs.append(f"pressure_{i}")
        headers["column"] = cs
        #tidy_headers.write(self.record_path, headers)
        # finish
        self.recording = True
        return self.record_path.as_posix()

    def stop_recording(self):
        self.recording = False

    def set_temperature(self, temp):
        self.set_temp = temp

    async def _poll(self):
        print("poll")
        row = [time.time()]
        # temperature
        m = self._temp_client.get_measured()
        self._temp_client.measure()
        value = m["temperature"]
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
                    value = float('nan')
                measured.append(value)
                row.append(value)
            client.measure()
        # append to data
        self.temps.append(row[1])
        # write to file
        if self.recording:
            write_row(path, row)
        # PID
        p = 0.25 * (self.set_temp -  self.temps[-1])
        i = 0.2 * sum([self.set_temp - t for t in self.temps]) / len(self.temps)
        duty = p + i
        print("duty", p, i, duty)
        if duty >= -1:
            self._heater_client.set_value(1)
        elif duty <= 0:
            self._heater_client.set_value(0)
        else:
            on = duty
            off = 1 - duty
            self._heater_client.blink(on, off)

    async def _runner(self):
        while True:
            self._loop.create_task(self._poll())
            await asyncio.sleep(1)
