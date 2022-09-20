import threading
import time

from miio import MiotDevice, AirPurifierMiot
# https://gist.github.com/wolever/e894d3a956c15044b2e4708f5e9d204d
from threading import Event
from abc import abstractmethod
from typing import Type,Callable, Any
from enum import Enum


class ParameterDBMap(Enum):
    AIR_TEMPERATURE = 'trj__at'
    RELATIVE_HUMIDITY = 'trj__rh'
    AIR_QI = 'trj__aqi'


class DeviceMonitor(threading.Thread):

    def __init__(self, poll_freq: int, device:  MiotDevice):
        super().__init__()

        # Polling frequency per minute
        self._poll_freq: int = poll_freq

        # The smart device we are monitoring
        self._device: MiotDevice = device

        self.__stop_event: Event = Event()

    def start(self):
        self.run()

    def run(self):
        while not self.__stop_event:
            # Do work specific to the sensor (to be overridden)
            self._work()

            # Put the thread to sleep
            time.sleep(self._poll_freq * 60)

    def stop(self):
        self.__stop_event.set()

    @abstractmethod
    def _work(self):
        pass


class AirPurifierDeviceMonitor(DeviceMonitor):

    def __init__(self, poll_freq: int, device: AirPurifierMiot):
        super().__init__(poll_freq, device)

        # self._device: AirPurifierMiot = device

    def _work(self):
        status = self._device.status()

        # parse status, save to db
