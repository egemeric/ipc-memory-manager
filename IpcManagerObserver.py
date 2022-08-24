import json
from multiprocessing.shared_memory import SharedMemory
from IpcManager import SharedMemorySlots, SharedMemoryDriver
from threading import Thread
from time import sleep


class Subject:
    _observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            print("Value Error")

    def notify(self, **kwargs):
        for observer in self._observers:
            observer.update(**kwargs)


class MemorySubject(Subject, Thread):
    MemoryAddress = None
    MemoryDriver = None
    _CheckInterval = 0.5
    _run = False
    _tracker_val = None

    def _memory_checker_job(self):
        while(self._run):
            self.MemoryDriver.update_self()
            live = self.MemoryDriver.get_slot_modified_times(
                self.MemoryAddress)
            if live != self._tracker_val:
                self._tracker_val = live
                data = self.MemoryDriver.read_data(self.MemoryAddress)
                # value has changed
                self.notify(**{'data': data})
            sleep(self._CheckInterval)

    def __init__(self, memory_address, memory_driver):
        self.MemoryAddress = memory_address
        self.MemoryDriver = memory_driver

    def run(self):
        self._run = True
        self._memory_checker_job()

    def setCheckInterval(self, interval):
        self._CheckInterval = interval


class Observer:

    def __init__(self) -> None:
        pass

    def update(self, **kwargs):
        pass


class MemoryObserver(Observer):
    Address = None

    def __init__(self) -> None:
        super().__init__()

    def update(self, **kwargs):
        data = kwargs['data']
        print("!--Data has changed--!")
        print(json.loads(data))
        pass


