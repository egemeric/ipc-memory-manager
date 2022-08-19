from curses.ascii import BEL
from enum import Enum
import struct
from multiprocessing import shared_memory, resource_tracker
from time import sleep


class SharedMemorySlots(Enum):
    MAIN = 0
    REALTIME = 1
    QUEUE = 2
    UNUSED = 3

    @classmethod
    def get(cls):
        return(cls.QUEUE, cls.REALTIME, cls.UNUSED)


class MemoryDriver():
    _Manager = None
    SLOTS = {}
    _master_mem = None

    def _update_self(self):
        raw_slots = self._master_mem.read_data()
        for is_active, address, size, modified_times, dynamic_size in raw_slots:
            slot = self.SLOTS[address]
            slot.is_active = is_active
            slot.size = size
            slot.modified_times = modified_times
            slot.dynamic_size = dynamic_size

    def _set_active_slots(self):
        slots = []
        raw_slots = self._master_mem.read_data()
        for is_active, address, size, modified_times, dynamic_size in raw_slots:
            a_slot = MemSlot(address, size)
            a_slot.is_active = is_active
            a_slot.modified_times = modified_times
            a_slot.dynamic_size = dynamic_size
            self.SLOTS[a_slot.address] = a_slot
            slots.append(a_slot)
        self._mem_mangr_update(slots)

    def _mem_mangr_update(self, slots):
        for slot in slots:
            self._Manager.update_block(slot=slot)
            slot.set_buffer(self._Manager.get_buffer(slot.address))
        pass

    def _activate(self, slot):
        slot.is_active = True
        # write other slot informations to master slot
        buffer = self._Manager.get_buffer(0)
        self._master_mem.write_data(slot)
        slot.set_buffer(self._Manager.get_buffer(slot.address))

    def write_data(self):
        pass

    def read_data(self):
        pass


class SharedMemoryDriver(MemoryDriver):
    DEFAULT_SLOT_SIZE = 1024

    def __init__(self, is_master=False):
        self.__boot(is_master)
    
    def __boot(self, is_master):
        self._master_mem = _MasterMemSlot()
        self._Manager = SharedMemoryManager(is_master)
        if self._Manager.InitializationNeeded:
            self._Manager.allocate(self._master_mem)
            self._master_mem.set_buffer(self._Manager.get_buffer(0))
            for address in SharedMemorySlots.get():
                self.SLOTS[address.value] = MemSlot(
                    address.value, SharedMemoryDriver.DEFAULT_SLOT_SIZE)
                self._Manager.allocate(self.SLOTS[address.value])
                self._activate(self.SLOTS[address.value])
        else:
            self._master_mem.set_buffer(self._Manager.get_buffer(0))
            self._set_active_slots()

    def write_data(self, address, data):
        self.SLOTS[address].write_data(data)
        self._master_mem.write_data(self.SLOTS[address])  # inform master
        self._update_self()

    def read_data(self, address):
        self._update_self()
        data = self.SLOTS[address].read_data()
        return data[5]

    def get_slot_modified_times(self, address):
        self._update_self()
        return self.SLOTS[address].modified_times


class _MasterMemSlot:
    modified_times = 0
    is_active = False
    Data = None
    Buffer_len = struct.calcsize("?IILL")
    _buffer = None
    dynamic_size = 0

    def __init__(self):
        self.address = 0
        self.size = self.Buffer_len * 4  # 4 slots are available

    def write_data(self, mem_slot):
        start_addres = mem_slot.address * self.Buffer_len
        end_address = start_addres + self.Buffer_len
        self._buffer[start_addres:end_address] = struct.pack(
            "?IILL", mem_slot.is_active, mem_slot.address, mem_slot.size, mem_slot.modified_times, mem_slot.dynamic_size)

    def read_data(self):
        result = []
        for addres in range(self.Buffer_len, self.size, self.Buffer_len):
            low = addres
            high = low + self.Buffer_len
            slot = struct.unpack("?IILL", self._buffer[low:high])
            result.append(slot)
        return tuple(result)

    def set_buffer(self, buff):
        self._buffer = buff

    def get_buffer(self):
        return self._buffer


class MemSlot(_MasterMemSlot):
    modified_times = 0
    is_active = False
    Data = None
    encoding = 'utf-8'

    def __init__(self, slot_address, size):
        self.address = slot_address
        self.size = size

    def write_data(self, string_data):
        self.modified_times += 1
        self.dynamic_size = self.Buffer_len + len(string_data)
        packed_data = struct.pack("?IILL" + str(len(string_data)) + 's', self.is_active, self.address,
                                  self.size, self.modified_times, self.dynamic_size, bytes(string_data, self.encoding))
        self._buffer[:self.dynamic_size] = packed_data
        return bytes(self._buffer[:self.Buffer_len])  # return header info

    def read_data(self):
        try:
            data = struct.unpack("?IILL" + str(self.dynamic_size -
                                               self.Buffer_len) + 's', self._buffer[:self.dynamic_size])
        except struct.error:
            return(self.is_active, self.address, self.size, self.modified_times, self.dynamic_size, b'')
        return(data)


class SharedMemoryManager:
    InitializationNeeded = False
    name_prefix = "app_shm_"
    entry_loc = None
    _BLOCKS = {}

    def __init__(self, is_master=False):
        self.is_master = is_master
        block_name = self.name_prefix+str(0)
        try:
            self._BLOCKS[0] = shared_memory.SharedMemory(block_name)
            resource_tracker.unregister("/"+block_name, 'shared_memory')

        except FileNotFoundError:
            self.InitializationNeeded = True
            pass

    def __del__(self):
        if self.is_master:
            print("Deallocate")
            self._BLOCKS[0].close()
            for address in self._BLOCKS.keys():
                self._BLOCKS[address].close()

    def allocate(self, memslot):
        block_name = self.name_prefix+str(memslot.address)
        try:
            self._BLOCKS[memslot.address] = shared_memory.SharedMemory(
                block_name)
            self.InitializationNeeded = False
            resource_tracker.unregister("/"+block_name, 'shared_memory')

        except FileNotFoundError:
            print("allocate:", block_name)
            self._BLOCKS[memslot.address] = shared_memory.SharedMemory(
                block_name, size=memslot.size, create=True)
            resource_tracker.unregister("/"+block_name, 'shared_memory')

    def get_buffer(self, address):
        return self._BLOCKS[address].buf

    def update_block(self, slot):
        block_name = self.name_prefix+str(slot.address)
        try:
            self._BLOCKS[slot.address] = shared_memory.SharedMemory(block_name)
            resource_tracker.unregister("/"+block_name, 'shared_memory')

        except FileNotFoundError:
            self._BLOCKS[slot.address] = shared_memory.SharedMemory(
                block_name, size=slot.size, create=True)
            resource_tracker.unregister("/"+block_name, 'shared_memory')



if __name__ == "__main__":
    driver = SharedMemoryDriver(is_master=True)
    while 1:
        sleep(1)
        pass
