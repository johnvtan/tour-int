class RingBuffer:
    def __init__(self, capacity):
        assert(capacity > 0)
        self.buffer = bytearray(capacity)
        self.read_index = 0
        self.count = 0
        self.capacity = capacity

    def __len__(self):
        return self.count

    def peek(self, num_bytes):
        ret = bytearray()
        if num_bytes > self.count:
            raise ValueError(
                'Tried to peek too many bytes from RingBuffer: buffer has {}, requested {}'
                .format(self.count, num_bytes)
            )

        read_start = self.read_index 
        read_end = (self.read_index + num_bytes) % self.capacity
        if read_end < read_start:
            ret.extend(self.buffer[read_start:self.capacity])
            ret.extend(self.buffer[:read_end])
        else:
            ret.extend(self.buffer[read_start:read_end])

        return ret

    def remove(self, num_bytes):
        self.read_index = (self.read_index + num_bytes) % self.capacity 
        self.count -= num_bytes

    def read(self, num_bytes):
        ret = self.peek(num_bytes)
        self.remove(num_bytes)
        return ret

    def write(self, data):
        if len(data) + self.count > self.capacity:
            raise ValueError(
                'Tried to write too many bytes to RingBuffer. ' +
                'Capacity = {}, Count = {}. data size = {}'
                .format(self.capacity, self.count, len(data))
            )

        write_start = (self.read_index + self.count) % self.capacity
        write_end = (write_start + len(data)) % self.capacity

        if write_end < write_start:
            num_before_end = self.capacity - write_start
            self.buffer[write_start:self.capacity] = data[:num_before_end]
            self.buffer[:write_end] = data[num_before_end:]
        else:
            self.buffer[write_start:write_end] = data

        self.count += len(data)

    def empty_space(self):
        return self.capacity - self.count

    def clear(self):
        self.count = 0
        self.read_index = 0

