from curses.ascii import BEL
from enum import Enum
import struct
from multiprocessing import shared_memory
from time import sleep


class SharedMemorySlots(Enum):
    MAIN = 0
    REALTIME = 1
    QUEUE = 2
    UNUSED = 3

    @classmethod
    def get(cls):
        return(cls.QUEUE, cls.REALTIME, cls.UNUSED)


class Driver():
    def activate(self):
        pass

    def deactivate(self):
        pass


class MemSlotDriver(Driver):
    MaxSlots = 4
    _Manager = None
    SLOTS = {}

    def __init__(self,is_master=False):
        self.__boot(is_master)

    def __boot(self,is_master):
        self.__master_mem = MasterMemSlot()
        self._Manager = SharedMemoryManager(is_master)
        if self._Manager.InitializationNeeded:
            self._Manager.allocate(self.__master_mem)
            for address in SharedMemorySlots.get():
                self.SLOTS[address.value] = MemSlot(address.value, 1024)
                self._Manager.allocate(self.SLOTS[address.value])
                self._activate(self.SLOTS[address.value])
        else:
            self._set_active_slots()

    def _set_active_slots(self):
        addresses = []
        buffer = self._Manager.get_buffer(0)
        raw_slots = self.__master_mem.read_data(buffer=buffer)
        for is_active, address, size, modified_times in raw_slots:
            a_slot = MemSlot(address, size)
            a_slot.is_active = is_active
            a_slot.modified_times = modified_times
            self.SLOTS[a_slot.address] = a_slot
            addresses.append(a_slot.address)
        self.__mem_mangr_update(adresses=addresses)
        print(self.SLOTS)

    def __mem_mangr_update(self, adresses):
        self._Manager.update_self(addresses=adresses)
        pass

    def _activate(self, slot):
        slot.is_active = True
        activation_pack = struct.pack(
            "?IIL", slot.is_active, slot.address, slot.size, slot.modified_times)
        buffer = self._Manager.get_buffer(0)
        self.__master_mem.write_data(slot, activation_pack, buffer)

    def deactivate(self, slot):
        slot.is_active = False
        return struct.pack("?IIL", slot.is_active, slot.address, slot.size, slot.modified_times)

    def pack_data(self):
        data = struct.pack("?IIL" + str(len(self.data)) + 's', self.is_active,
                           self.slot, self.size, self.modified_times, bytes(self.data))
        return data

    def unpack_data(self, data):
        data = struct.unpack(
            "?IIL" + str(len(data)-self.HEAD_SIZE + 's', data))
        return data


class MasterMemSlot:
    modified_times = 0
    is_active = False
    Data = None
    Buffer_len = struct.calcsize("?IIL")

    def __init__(self):
        self.address = 0
        self.size = self.Buffer_len * 4  # 4 slots are available

    def write_data(self, mem_slot, data, buffer):
        start_addres = mem_slot.address * self.Buffer_len
        end_address = start_addres + self.Buffer_len
        buffer[start_addres:end_address] = data

    def read_data(self, buffer):
        result = []
        for addres in range(self.Buffer_len, self.size, self.Buffer_len):
            low = addres
            high = low + self.Buffer_len
            slot = struct.unpack("?IIL", buffer[low:high])
            result.append(slot)
        return tuple(result)


class MemSlot():
    modified_times = 0
    is_active = False
    Data = None

    def __init__(self, slot_address, size):
        self.address = slot_address
        self.size = size


class SharedMemoryManager:
    InitializationNeeded = False
    name_prefix = "app_shm_"
    entry_loc = None
    _BLOCKS = {}

    def __init__(self,is_master=False):
        self.is_master = is_master
        block_name = self.name_prefix+str(0)
        try:
            self._BLOCKS[0] = shared_memory.SharedMemory(block_name)
        except FileNotFoundError:
            self.InitializationNeeded = True
            pass

    def __del__(self):
        if self.is_master:
            for address in self._BLOCKS.keys():
                self._BLOCKS[address].close()
                self._BLOCKS[address].unlink()

    def allocate(self, memslot):
        block_name = self.name_prefix+str(memslot.address)
        try:
            self._BLOCKS[memslot.address] = shared_memory.SharedMemory(
                block_name)
            self.InitializationNeeded = False
        except FileNotFoundError:
            print("allocate:", block_name)
            self._BLOCKS[memslot.address] = shared_memory.SharedMemory(
                block_name, size=memslot.size, create=True)

    def get_buffer(self, address):
        return self._BLOCKS[address].buf

    def update_self(self, addresses):
        for address in addresses:
            block_name = self.name_prefix+str(address)
            self._BLOCKS[address] = shared_memory.SharedMemory(block_name)


if __name__ == "__main__":
    driver = MemSlotDriver(is_master=True)
    while 1:
        sleep(1)
        pass
