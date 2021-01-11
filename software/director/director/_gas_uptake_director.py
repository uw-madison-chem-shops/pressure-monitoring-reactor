__all__ = ["GasUptakeDirector"]

import os
import time
import yaqc
import gpiozero
import asyncio
from typing import Dict, Any
import datetime
import collections
import pathlib
from simple_pid import PID
from yaqd_core import IsDaemon

from .__version__ import *

os.chdir(os.path.expanduser("~"))
data_directory = pathlib.Path("Desktop/gas-uptake-data")


def write_row(path, row):
    with open(path, "a") as f:
        for n in row:
            f.write("%8.6f" % n)
            f.write("\t")
        f.write("\n")


class GasUptakeDirector(IsDaemon):
    _kind = "gas-uptake-director"

    def __init__(self, name, config, config_filepath):
        self.i = 0
        super().__init__(name, config, config_filepath)
        self.recording = False
        self.temps = collections.deque(maxlen=500)
        self.set_temp = 0
        self.row = []
        #time.sleep(30)
        # initialize clients
        self._heater_client = gpiozero.DigitalOutputDevice(pin=18)  #yaqc.Client(38455)
        self._heater_client.value = 0
        self._temp_client = yaqc.Client(39001)
        self._temp_client.measure(loop=True)
        self._pressure_client_a = yaqc.Client(39100)
        #self._pressure_client_a.set_state(gain=2, size=16)
        self._pressure_client_a.measure(loop=True)
        self._pressure_client_b = yaqc.Client(39101)
        #self._pressure_client_b.set_state(gain=2, size=16)
        self._pressure_client_b.measure(loop=True)
        self._pressure_client_c = yaqc.Client(39102)
        #self._pressure_client_c.set_state(gain=2, size=16)
        self._pressure_client_c.measure(loop=True)
        # begin looping
        self._pid = PID(Kp=0.2, Ki=0.001, Kd=0.01, setpoint=0, proportional_on_measurement=True)
        self._loop.create_task(self._runner())

    def _connection_lost(self, peername):
        super()._connection_lost(peername)
        self.set_temp = 0

    def begin_recording(self):
        # create file
        now = datetime.datetime.now()
        fname = "gas-uptake_" + now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        self.record_path = data_directory / fname
        tab = "\t"
        newline = "\n"
        with open(self.record_path, "a") as f:
            f.write("timestamp:" + tab + "'" + now.isoformat() + "'" + newline)
            f.write("gas-uptake version:" + tab + "'" +  __version__ + "'" + newline)
            f.write("temperature units:" + tab + "'C'" + newline)
            f.write("pressure units:" + tab + "'PSI'" + newline)
            f.write("column:" + tab + "[")
            f.write("'labtime'")
            f.write(tab + "'temperature'")
            for i in range(12):
                f.write(tab + f"'pressure_{i}'")
            f.write("]" + newline)
        # finish
        self.recording = True
        return self.record_path.as_posix()

    def stop_recording(self):
        self.recording = False

    def set_temperature(self, temp):
        self.set_temp = temp
        self._pid.reset()

    async def _poll(self):
        row = [time.time()]
        # temperature
        m = self._temp_client.get_measured()
        value = m["temperature"]
        row.append(value)
        # pressure
        measured = []
        i = 0
        self._last_pressure_readings = dict
        for client in [
            self._pressure_client_a,
            self._pressure_client_b,
            self._pressure_client_c,
        ]:
            m = client.get_measured()
            for channel in range(4):
                value = m[f"channel_{channel}"]
                offset = self._state[f"channel_{i}_offset"]; i += 1
                value -= offset
                value -= 4
                value *= 150 / 20  # mA to PSI
                if value < 0:
                    value = float('nan')
                measured.append(value)
                self._last_pressure_readings[i] = value
                row.append(value)
        # append to data
        self.temps.append(row[1])
        self.row = row
        # write to file
        if self.recording:
            write_row(self.record_path, row)
        # PID
        self._pid.setpoint = self.set_temp
        duty = self._pid(row[1])
        print(self.set_temp, row[1], duty, self._pid.components)
        if duty >= 1:
            self._heater_client.value = 1
        elif duty <= 0:
            self._heater_client.value = 0
        else:
            duty = round(duty, 2)
            self._heater_client.blink(on_time=duty, off_time=10, n=1)

    async def _runner(self):
        while True:
            self._loop.create_task(self._poll())
            await asyncio.sleep(1)

    def get_last_reading(self):
        return self.row

    def tare_pressure(self, known_value, channel_index):
        """Apply offset channel based on known pressure value.

        Parameters
        ----------
        known_value : double
            Known pressure, PSI.
        channel_index : int
            Channel index, 0 through 11.
        """
        # convert from PSI to expected mA
        value = known_value * 20 / 150
        value += 4
        # find offset
        offset = self._last_pressure_readings[channel_index] - value
        self._state[f"channel_{channel_index}_offset"] = offset
