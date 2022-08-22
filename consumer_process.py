from IpcManager import SharedMemoryDriver, SharedMemorySlots
from IpcManagerObserver import MemorySubject, MemoryObserver


if __name__ == '__main__':
    memoryDriver = SharedMemoryDriver(is_master=False)
    subj = MemorySubject(SharedMemorySlots.REALTIME.value,
                         memory_driver=memoryDriver)
    observer = MemoryObserver()
    subj.attach(observer=observer)
    subj.run()
