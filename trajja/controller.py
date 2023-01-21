import datetime
import logging
import threading
import time

from miio import MiotDevice, AirPurifierMiot
from threading import Event
from abc import abstractmethod
from typing import Type,Callable, Any
from enum import Enum

from dataclasses import dataclass


@dataclass
class DevicePayload:
    """
    Class to encapsulate the output from a smart device
    """
    device_id: str
    device_ip: str
    is_error: bool
    is_on: bool
    timestamp: datetime.datetime
    parameters: dict


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
        """

        :type device: object
        """

        super().__init__(poll_freq, device)

        self._device: AirPurifierMiot = device

        self._parameters_keys = ['relative_humidity', 'temperature', 'target_humidity',
                                 'water_shortage_fault']

    def _work(self):
        device_status = self._device.status()

        # parse status, save to db

        device_id: response.id
        device_ip: str
        is_error: bool
        is_on: bool
        timestamp: datetime.datetime
        parameters: dict

        db.save()

        if response['error']:
            logging.warning(f"{self._device.model} at {self._device.ip} is in error")

        return DevicePayload(
            self._device.device_id, self._device.ip, response['error']
        )
