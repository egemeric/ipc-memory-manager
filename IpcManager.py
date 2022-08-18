from enum import Enum
import struct
from multiprocessing import shared_memory,


class SharedMemorySlots(Enum):
    REALTIME = 1
    QUEUE = 2

    @classmethod
    def get(cls):
        return(cls.QUEUE, cls.REALTIME)


class Driver():
    def activate(self):
        pass

    def deactivate(self):
        pass


class MemSlotDriver(Driver):
    MaxSlots = 4
    Manager = None
    SLOTS = {}

    def __init__(self):
        self.__boot()

    def __boot(self):
        print("boot")
        test = [0, 0, 0]
        self.__master_mem = MasterMemSlot()
        self.Manager = SharedMemoryManager()
        self.Manager.allocate(self.__master_mem)
        for address in SharedMemorySlots.get():
            self.SLOTS[address.value] = MemSlot(address.value, 1024)
            self.Manager.allocate(self.SLOTS[address.value])
            self._activate(self.SLOTS[address.value])

    def _activate(self, slot):
        slot.is_active = True
        activation_pack = struct.pack(
            "?IIL", slot.is_active, slot.address, slot.size, slot.modified_times)
        buffer = self.Manager.get_buffer(0)
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
        print(bytearray(buffer[:]))

    def read_data(self, data):
        pass


class MemSlot():
    modified_times = 0
    is_active = False
    Data = None

    def __init__(self, slot_address, size):
        self.address = slot_address
        self.size = size


class SharedMemoryManager:
    name_prefix = "app_shm_"
    entry_loc = None
    _BLOCKS = {}

    def __init__(self):
        pass

    def __del__(self):
        for address in self._BLOCKS.keys():
            self._BLOCKS[address].close()
            self._BLOCKS[address].unlink()

    def allocate(self, memslot):
        block_name = self.name_prefix+str(memslot.address)
        print("allocate:", block_name)
        try:
            self._BLOCKS[memslot.address] = shared_memory.SharedMemory(
                block_name)
        except FileNotFoundError:
            self._BLOCKS[memslot.address] = shared_memory.SharedMemory(
                block_name, size=memslot.size, create=True)

    def get_buffer(self, address):
        return self._BLOCKS[address].buf


if __name__ == "__main__":
    driver = MemSlotDriver()
