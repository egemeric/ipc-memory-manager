#!/usr/bin/python
# Shared memory reader
from datetime import datetime
import json
from time import sleep, time
import IpcManager

if __name__ == "__main__":
    mng = IpcManager.SharedMemoryDriver(is_master=False)
    counter = 0
    changed_times = None
    check = None
    while 1:
        check = mng.get_slot_modified_times(IpcManager.SharedMemorySlots.REALTIME.value)
        if changed_times != check:
            changed_times = check
            try:
                data = mng.read_data(IpcManager.SharedMemorySlots.REALTIME.value)
                print("Slot's data is changed.")
                print(data)
                print("----------------")
            except Exception as e:
                pass
           
        sleep(0.1)
        
