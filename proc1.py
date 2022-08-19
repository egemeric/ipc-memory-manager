#!/usr/bin/python
# Master Proccess
from datetime import datetime
import json
from time import sleep, time
import IpcManager

if __name__ == "__main__":
    mng = IpcManager.SharedMemoryDriver(is_master=True)
    counter = 0
    while 1:
        counter += 1
        data = {"time":str(datetime.now()), "counter":counter, "data":"abcgsgdh"}
        data = json.dumps(data)
        mng.write_data(IpcManager.SharedMemorySlots.REALTIME.value,data=data)
        sleep(1)
