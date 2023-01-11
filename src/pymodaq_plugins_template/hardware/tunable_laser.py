# -*- coding: utf-8 -*-
"""
Created the 11/01/2023

@author: Sebastien Weber
"""
import pyvisa
from pyvisa.resources.tcpip import TCPIPInstrument
from pymodaq.daq_utils.enums import BaseEnum

visa_rm = pyvisa.ResourceManager()
ressources = visa_rm.list_resources()
"""
The ressources as returned from the ressource manager is of type TCP. Even if connected with USB
 it somehow emulates a TCP connection. The address returned is including the instrument
model name in the address: 'TCPIP0::K-N7778C-00303::inst0::INSTR'
That address cannot be opened with pyvisa (don't know why yet)
One should use the IP adress: 'TCPIP0::100.65.25.37::inst0::INSTR'
"""
VISA_ADDRESS = 'TCPIP0::100.65.25.37::inst0::INSTR'


class TriggerOutput(BaseEnum):
    DISABLED = 0  #DISabled: Never.
    STFINISHED = 1  #STFinished When a sweep step finishes.
    SWFINISHED = 2  # SWFinished When sweep cycle finishes.
    SWSTART = 3  # SWSTarted When a sweep cycle starts.


class SweepMode(BaseEnum):
    STEP = 0
    MAN = 1
    CONT = 2


class TunableLaser:

    def __init__(self):
        self.device: TCPIPInstrument = None
        self._wavelength: float = None
        self._idn: str = None

    def _write(self, message: str):
        if self.device is not None:
            self.device.write(message)

    def _read(self) -> str:
        if self.device is not None:
            return self.device.read().strip('\n')

    def _read_number(self) -> float:
        if self.device is not None:
            return self.device.read_ascii_values()[0]

    def open_communication(self, address: str = VISA_ADDRESS):
        self.device: TCPIPInstrument = visa_rm.open_resource(address)
        self._write('*IDN?')
        self._idn = self._read()
        return self._idn

    @property
    def wavelength(self):
        """get/set the wavelength in nanometer"""
        self._write(':SOURce0:WAVelength?')
        self._wavelength = self._read_number() * 1e9
        return self._wavelength

    @wavelength.setter
    def wavelength(self, wavelength: float):
        self._write(f':SOURce0:WAVelength {wavelength}NM')
        self.wavelength

    def get_wavelength_limits(self):
        self._write(f':SOURce0:WAVelength? MIN')
        min_val = self._read_number()

        self._write(f':SOURce0:WAVelength? MAX')
        max_val = self._read_number()
        return min_val, max_val

    @property
    def output_trigger(self) -> TriggerOutput:
        self._write(f':TRIG0:OUTP?')
        trig = self._read().upper()
        return TriggerOutput[trig]

    @output_trigger.setter
    def output_trigger(self, trigger: TriggerOutput):
        self._write(f':TRIG0:OUTP {trigger.name}')

    @property
    def sweep_cycles(self) -> int:
        self._write(f':SOURce0:WAVelength:SWEep:CYCLes?')
        return int(self._read_number())

    @sweep_cycles.setter
    def sweep_cycles(self, ncycles: int = 1):
        self._write(f':SOURce0:WAVelength:SWEep:CYCLes {ncycles}')

    @property
    def sweep_mode(self) -> SweepMode:
        self._write(f':SOURce0:WAVelength:SWEep:MODE?')
        return SweepMode[self._read().upper()]

    @sweep_mode.setter
    def sweep_mode(self, mode: SweepMode):
        self._write(f':SOURce0:WAVelength:SWEep:MODE {mode.name}')

    @property
    def sweep_speed(self):
        """get/set the weeping speed in nm/s"""
        self._write(f':SOURce0:WAVelength:SWEep:SPEed?')
        return self._read_number() * 1e9

    @sweep_speed.setter
    def sweep_speed(self, speed: float):
        self._write(f':SOURce0:WAVelength:SWEep:SPEed {speed}NM/S')

    def configure_sweep(self, start: float, stop: float, step: float):
        """configure the sweep with values in nanomaters"""
        self._write(f':SOURce0:WAVelength:SWEep:STEP {step}NM')
        self._write(f':SOURce0:WAVelength:SWEep:STARt {start}NM')
        self._write(f':SOURce0:WAVelength:SWEep:STOP {stop}NM')

        self._write(f':SOURce0:WAVelength:SWEep:STARt?')
        start = self._read_number() * 1e9

        self._write(f':SOURce0:WAVelength:SWEep:STEP?')
        step = self._read_number() * 1e9

        self._write(f':SOURce0:WAVelength:SWEep:STOP?')
        stop = self._read_number() * 1e9

        return start, stop, step

    def start_sweep(self):
        self._write(f':SOURce0:WAVelength:SWEep STARt')

    @property
    def laser_status(self) -> bool:
        self._write(f':SOURce0:POWer:STATe?')
        return bool(int(self._read_number()))

    @laser_status.setter
    def laser_status(self, status: bool = True):
        status = 1 if status is True else 0
        self._write(f':SOURce0:POWer:STATe {status}')

    @property
    def locked(self) -> bool:
        self._write(f':LOCK?')
        return bool(int(self._read_number()))

    @locked.setter
    def locked(self, lock: bool = False) -> bool:
        status = 1 if lock is True else 0
        self._write(f':LOCK {status},1234')

    def close_communication(self):
        self.device.close()

    def __repr__(self):
        return f'{self.__class__.__name__}:{self._idn} at {self._wavelength}nm'


if __name__ == '__main__':
    laser = TunableLaser()
    idn = laser.open_communication(VISA_ADDRESS)
    print(f'Device: {idn} opened')
    print(laser.wavelength)
    print(laser.get_wavelength_limits())
    print(laser.output_trigger)

    print(laser.sweep_mode)
    laser.sweep_mode = SweepMode['CONT']
    print(laser.sweep_mode)

    print(laser.configure_sweep(1460, 1620, 10))

    print(laser.locked)
    laser.locked = True
    print(laser.locked)
    laser.locked = False
    print(laser.locked)

    print(laser.laser_status)
    laser.laser_status = True
    print(laser.laser_status)
    laser.laser_status = False
    print(laser.laser_status)
    print(laser.sweep_cycles)
    laser.sweep_cycles = 2
    print(laser.sweep_cycles)
    pass
    laser.close_communication()
