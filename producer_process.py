#!/usr/bin/python
# Master Proccess
from datetime import datetime
import json
from time import sleep, time
import IpcManager
import random
import string

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    result_str += 'çşğü?'
    return result_str

if __name__ == "__main__":
    mng = IpcManager.SharedMemoryDriver(is_master=True)
    counter = 0
    while 1:
        counter += 1
        data = {"time":str(datetime.now()), "counter":counter, "data":get_random_string(10)}
        data = json.dumps(data)
        mng.write_data(IpcManager.SharedMemorySlots.REALTIME.value,data=data)
        sleep(1)
