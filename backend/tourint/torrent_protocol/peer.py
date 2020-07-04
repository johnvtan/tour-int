from typing import Dict, Tuple
from queue import Queue
import socket
import sys
import random
import enum
import time
import hashlib

if __package__ is None or __package__ == '':
    import consts
    import tracker
    import ring_buffer
else:
    from . import consts
    from . import tracker
    from . import ring_buffer

def read_from_socket_checked(s: socket.socket, size_bytes: int) -> bytes:
    ret = bytearray()
    while size_bytes:
        received = s.recv(size_bytes)
        if len(received) == 0:
            raise ValueError('Error: socket closed connection')
        ret.extend(received)
        size_bytes -= len(received)
    return ret

class PeerHandshake:
    PEER_ID_LEN: int = 20
    INFO_HASH_LEN: int = 20

    HANDSHAKE_SIZE: int = 68
    NAME_LENGTH: int = 19
    PROTOCOL_NAME: str = 'BitTorrent protocol'
    RESERVED_SIZE: int = 8

    def __init__(self, peer_id: bytearray, info_hash: bytearray):
        assert(len(peer_id) == self.PEER_ID_LEN)
        assert(len(info_hash) == self.INFO_HASH_LEN)

        self.peer_id = peer_id
        self.info_hash = info_hash

    def __str__(self):
        return 'PeerHandshake: id = {}, hash = {}'.format(self.peer_id, self.info_hash)

    def serialize(self) -> bytes:
        b: bytearray = bytearray([self.NAME_LENGTH])
        b.extend(self.PROTOCOL_NAME.encode('ascii'))
        b.extend(bytearray(self.RESERVED_SIZE))
        b.extend(self.info_hash)

        if isinstance(self.peer_id, bytes):
            b.extend(self.peer_id)
        elif isinstance(self.peer_id, str):
            b.extend(self.peer_id.encode('ascii'))
        elif isinstance(self.peer_id, int):
            b.extend(self.peer_id.to_bytes(self.PEER_ID_LEN, byteorder='big'))
        else:
            raise ValueError('unknown type of peer_id: {}'.format(type(self.peer_id)))

        assert(len(b) == self.HANDSHAKE_SIZE)
        return bytes(b)
    
    @classmethod
    def deserialize(cls, handshake_bytes: bytes):
        """Deserializes a handshake from bytes.

        Raises a ValueError if handshake_bytes isn't the correct format
        """
        if len(handshake_bytes) != cls.HANDSHAKE_SIZE:
            raise ValueError('PeerHandshake.deserialize: expected {} bytes, but got\
                    {}'.format(cls.HANDSHAKE_SIZE, len(handshake_bytes)))

        idx = 0
        protocol_name_length: int = handshake_bytes[idx] 

        if protocol_name_length != cls.NAME_LENGTH:
            raise ValueError('PeerHandshake.deserialize: expected name length is {}, but got\
                    {}'.format(cls.NAME_LENGTH, protocol_name_length))

        idx += 1
        protocol_name: str = handshake_bytes[idx:idx+protocol_name_length].decode(encoding='ascii')
        if protocol_name != cls.PROTOCOL_NAME:
            raise ValueError('PeerHandshake.deserialize: expected protocol name {} but got\
                    {}'.format(cls.PROTOCOL_NAME, protocol_name))

        idx += cls.NAME_LENGTH 
        # skipping reserved bytes
        idx += cls.RESERVED_SIZE

        info_hash = handshake_bytes[idx:idx+cls.INFO_HASH_LEN]
        idx += cls.INFO_HASH_LEN

        peer_id = handshake_bytes[idx:idx+cls.PEER_ID_LEN]

        return cls(peer_id, info_hash)


class PeerMessage:
    MESSAGE_LENGTH_SIZE: int = 4

    class Id(enum.Enum):
        # len == 1
        CHOKE = 0
        UNCHOKE = 1
        INTERESTED = 2
        NOT_INTERESTED = 3

        # variable len
        HAVE = 4
        BITFIELD = 5
        REQUEST = 6
        PIECE = 7
        CANCEL = 8
        PORT = 9 

        # len == 0
        KEEP_ALIVE = 10


    def __init__(self, message_id, payload=None):
        self.id = message_id
        self.payload = payload

    def __str__(self):
        return 'PeerMessage {}, payload = {}'.format(self.id, self.payload)

    @classmethod
    def is_state_message(cls, message_id):
        return message_id in [cls.Id.CHOKE, cls.Id.UNCHOKE, cls.Id.INTERESTED, cls.Id.NOT_INTERESTED]

    @classmethod
    def is_valid_message_id(cls, message_id):
        valid_values = [t.value for t in cls.Id]
        return message_id in valid_values

    def serialize(self) -> bytes:
        if self.id == self.Id.KEEP_ALIVE:
            return bytearray(MESSAGE_LENGTH_SIZE)

        ret = bytearray()

        message_length = 1 if not self.payload else 1 + len(self.payload)
        ret.extend(message_length.to_bytes(self.MESSAGE_LENGTH_SIZE, byteorder='big'))
        ret.extend(self.id.value.to_bytes(1, byteorder='big'))
        if self.payload:
            ret.extend(self.payload)
        return bytes(ret)

    @classmethod
    def new_request(cls, piece_index, begin, length):
        payload = bytearray()
        payload.extend(piece_index.to_bytes(4, byteorder='big'))
        payload.extend(begin.to_bytes(4, byteorder='big'))
        payload.extend(length.to_bytes(4, byteorder='big'))
        return cls(cls.Id.REQUEST, payload=payload)

    @classmethod
    def from_ring_buffer(cls, buf):
        """Parses a PeerMessage from a ring_buffer

        A full message including the payload must be in buf.

        Returns None if there isn't enough data in the buffer
        """
        if len(buf) < cls.MESSAGE_LENGTH_SIZE:
            return None
        
        message_length_bytes = buf.peek(cls.MESSAGE_LENGTH_SIZE)
        message_length = int.from_bytes(message_length_bytes, byteorder='big')

        if message_length == 0:
            buf.remove(cls.MESSAGE_LENGTH_SIZE)
            return cls(cls.Id.KEEP_ALIVE, 0)
        
        if message_length > 20000:
            raise Exception('shouldnt happen')

        #print('message length {}'.format(message_length))
        if len(buf) < message_length + cls.MESSAGE_LENGTH_SIZE:
            # Incomplete header
            # Don't remove anything from the buffer, wait for next byte to get a full header
            #print('incomplete header: buffer needs {} bytes but only has {}'.format(message_length + 4,
            #    len(buf)))
            return None


        # Have a full header (length + message id)
        buf.remove(cls.MESSAGE_LENGTH_SIZE)
        message_id = cls.Id(buf.read(1)[0])

        payload_length = message_length - 1
        assert(len(buf) >= payload_length)

        payload = buf.read(payload_length)
        return cls(message_id, payload)
    
    
class Bitfield:
    def __init__(self, bitfield_bytes):
        assert(bitfield_bytes is not None)
        self.bitfield_bytes = bitfield_bytes

    @staticmethod
    def get_idx_and_offset(bitfield_index) -> Tuple[int, int]:
        byte_index = bitfield_index // 8
        offset = bitfield_index % 8
        return byte_index, (7-offset)

    def contains(self, index) -> bool:
        index, offset = self.get_idx_and_offset(index)
        return ((self.bitfield_bytes[index] >> offset) & 1) > 0

    def set(self, index):
        index, offset = self.get_idx_and_offset(index)
        self.bitfield_bytes[index] |= (1 << offset)

    def clear(self, index):
        index, offset = self.get_idx_and_offset(index)
        self.bitfield_bytes[index] &= ~(1 << offset)

class PieceDownload:
    BLOCK_SIZE_BYTES: int = 16384
    def __init__(self, piece_index, piece_size_bytes):
        # TODO handle next requested byte better. A set maybe?
        self.piece_index = piece_index
        self.piece_bytes = bytearray(piece_size_bytes)

        num_blocks = piece_size_bytes // self.BLOCK_SIZE_BYTES 
        if piece_size_bytes % self.BLOCK_SIZE_BYTES:
            num_blocks += 1
        
        self.total_num_blocks = num_blocks
        self.blocks_to_request = set(range(num_blocks))
        self.blocks_received = set()

    def get_next_block_request(self) -> PeerMessage: 
        next_block = next(iter(self.blocks_to_request))

        start_byte = next_block * self.BLOCK_SIZE_BYTES
        if start_byte + self.BLOCK_SIZE_BYTES > len(self.piece_bytes):
            length = len(self.piece_bytes) - start_byte
        else:
            length = self.BLOCK_SIZE_BYTES

        ret = PeerMessage.new_request(self.piece_index, start_byte, length)
        self.blocks_to_request.remove(next_block)
        return ret 

    def handle_block_response(self, payload):
        piece_index = int.from_bytes(payload[0:4], byteorder='big')
        assert(piece_index == self.piece_index)

        start_byte = int.from_bytes(payload[4:8], byteorder='big')

        end_byte = start_byte + len(payload[8:])

        if end_byte > len(self.piece_bytes):
            raise ValueError('End byte too large: got {}, max: {}'.format(end_byte,
                len(self.piece_bytes)))

        self.piece_bytes[start_byte:end_byte] = payload[8:]

        received_block = start_byte // self.BLOCK_SIZE_BYTES
        self.blocks_received.add(received_block)

    def all_blocks_received(self):
        return len(self.blocks_received) == self.total_num_blocks

    def has_more_blocks_to_request(self):
        return len(self.blocks_to_request) > 0 

class PeerConnection:
    """Manages a connection and piece downloads from a peer"""

    # Timeout time in seconds in case a peer fails to connect
    CONNECTION_TIMEOUT_S: int = 5
    MAX_QUEUED_REQUESTS: int = 10
    BUFFER_PADDING: int = 1024 

    class State(enum.Enum):
        INIT_HANDSHAKE = 0
        INIT_BITFIELD = 1
        DOWNLOADING = 2
        IDLE = 3
        PAUSED = 4
        CANCEL = 5
        DISCONNECTED = 6

    def __init__(self, peer_info: Dict, info_hash: bytearray, piece_length):
        self.peer_info = peer_info
        self.info_hash = info_hash
        self.piece_length = piece_length

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.choked = True

        self.peer_id = None

        self.num_queued_requests = 0
        self.buffer = ring_buffer.RingBuffer(PieceDownload.BLOCK_SIZE_BYTES + self.BUFFER_PADDING)

        self.available_pieces = None
        self.state: self.State = self.State.DISCONNECTED 
        self.download_state = None

    def __str__(self):
        return "PeerConnection on IP = {}:{} for hash {}".format(self.peer_info['ip'],
                self.peer_info['port'], self.info_hash)

    def initialize_connection(self):
        """
        Begin handshaking sequence, change state to initialized
        """
        # TODO how to track state of connection if this fails?
        assert(self.state == self.State.DISCONNECTED)

        self.socket.settimeout(self.CONNECTION_TIMEOUT_S)
        self.socket.connect((self.peer_info['ip'], self.peer_info['port']))

        # Get to initializing state once connection succeeds
        self.state = self.State.INIT_HANDSHAKE

        handshake = PeerHandshake(consts.PEER_ID, self.info_hash)
        self.socket.send(handshake.serialize())

   
    def validate_handshake(self) -> bool:
        if len(self.buffer) < PeerHandshake.HANDSHAKE_SIZE:
            return

        received = self.buffer.read(PeerHandshake.HANDSHAKE_SIZE)
        handshake = PeerHandshake.deserialize(received)
        if handshake.info_hash != self.info_hash:
            self.state = self.State.DISCONNECTED
            return
        
        self.peer_id = handshake.peer_id
        self.state = self.State.INIT_BITFIELD

    def peer_has_piece(self, index):
        if not self.available_pieces:
            raise ValueError('Bitfield not initialized')
        return self.available_pieces.contains(index)

    def handle_state_message(self, message_id):
        if message_id == PeerMessage.Id.CHOKE:
            self.choked = True
        elif message_id == PeerMessage.Id.UNCHOKE:
            self.choked = False
        elif message_id == PeerMessage.Id.INTERESTED:
            pass
        elif message_id == PeerMessage.Id.NOT_INTERESTED:
            pass

    def handle_bitfield(self, payload):
        if self.available_pieces is not None:
            raise ValueError('Error: erroneous bitfield message?')
        self.available_pieces = Bitfield(payload)

    def handle_have(self, payload):
        assert(len(payload) == 4)
        assert(self.available_pieces is not None)
        new_piece_index = int.from_bytes(payload, byteorder='big')
        self.available_pieces.set(new_piece_index)

    def handle_piece(self, payload, download_state):
        download_state.handle_block_response(payload)
        self.num_queued_requests -= 1
    
    def send_block_requests(self, download_state):
        while self.num_queued_requests < self.MAX_QUEUED_REQUESTS:
            if not download_state.has_more_blocks_to_request():
                break
            next_request = download_state.get_next_block_request()
            self.socket.send(next_request.serialize())
            self.num_queued_requests += 1

    def start_piece_download(self, piece_index):
        assert(self.state == self.State.IDLE)
        assert(self.peer_has_piece(piece_index))
        
        print('Starting download on piece {}'.format(piece_index))
        self.state = self.State.DOWNLOADING
        self.download_state = PieceDownload(piece_index, self.piece_length)
        if not self.choked:
            self.send_block_requests(self.download_state)
    
    def is_idle(self):
        return self.state == self.State.IDLE

    def append_to_buffer(self, data):
        self.buffer.write(data)

    def get_piece_bytes(self):
        if not self.is_download_completed():
            print('Error: can\'t get piece bytes if download not complete')
            return None
        return self.download_state.piece_bytes
    
    def get_current_piece_index(self):
        if not self.download_state:
            return -1
        return self.download_state.piece_index

    def set_paused(self):
        self.state = self.State.PAUSED

    def set_disconnected(self):
        # TODO send cancel command, or maybe just disconnect?
        # not sure how to disconnect from socket gracefully
        # TODO close socket here?
        self.socket.close()
        self.buffer.clear()
        self.state = self.State.DISCONNECTED

    def is_download_completed(self):
        if not self.download_state:
            #print('Err: no initialized download')
            return False

        return self.download_state.all_blocks_received() and self.state == self.State.IDLE
    
    def is_disconnected(self):
        return self.state == self.State.DISCONNECTED

    def run_init_states(self):
        if self.state == self.State.INIT_HANDSHAKE:
            self.validate_handshake()
        elif self.state == self.State.INIT_BITFIELD:
            message = PeerMessage.from_ring_buffer(self.buffer)
            if not message:
                return

            if message.id != PeerMessage.Id.BITFIELD:
                print('Error! {} expected bitfield msg but got {}'.format(str(self), message.id))
                self.set_disconnected()
                return
            
            self.handle_bitfield(message.payload)
            self.state = self.State.IDLE
            self.socket.settimeout(None)
            self.socket.send(PeerMessage(PeerMessage.Id.INTERESTED, None).serialize())


    def handle_messages_from_buffer(self, handle_piece_message):
        if self.state == self.State.DISCONNECTED:
            return

        # Parse all messages from buffer regardless of state
        # Except Piece messages, which are only handled in downloading state
        # and should be thrown away otherwise
        while len(self.buffer) > 0:
            message = PeerMessage.from_ring_buffer(self.buffer)
            if message is None:
                break

            if PeerMessage.is_state_message(message.id):
                self.handle_state_message(message.id)
            elif message.id == PeerMessage.Id.BITFIELD:
                self.handle_bitfield(message.payload)
            elif message.id == PeerMessage.Id.HAVE:
                self.handle_have(message.payload)
            elif message.id == PeerMessage.Id.PIECE and handle_piece_message:
                self.handle_piece(message.payload, self.download_state)

    def run_download_state(self):
        assert(self.state == self.State.DOWNLOADING)
        self.handle_messages_from_buffer(True)
        if not self.choked:
            self.send_block_requests(self.download_state)

        if self.download_state.all_blocks_received():
            self.state = self.State.IDLE

    def run_pause_state(self, send_keep_alive=False):
        assert(self.state == self.State.PAUSED)
        self.handle_messages_from_buffer(False)
        if send_keep_alive:
            self.socket.send(PeerMessage(PeerMessage.Id.KEEP_ALIVE).serialize())

    def run_idle_state(self):
        assert(self.state == self.State.IDLE)
        self.handle_messages_from_buffer(False)

    def read_from_socket(self):
        recv_length = self.buffer.empty_space()
        if recv_length == 0:
            print('buffer full pray 2 jesus there\'s a full message in there')
            return

        recv = self.socket.recv(recv_length)

        if len(recv) == 0:
            self.set_disconnected()
            return

        self.append_to_buffer(recv)

    def run_state_machine(self):
        if self.state == self.State.INIT_HANDSHAKE or self.state == self.State.INIT_BITFIELD:
            self.run_init_states()
        elif self.state == self.State.IDLE:
            self.run_idle_state()
        elif self.state == self.State.PAUSED:
            self.run_pause_state()
        elif self.state == self.State.DOWNLOADING:
            self.run_download_state()

    
if __name__ == '__main__':
    metainfo: Dict = tracker.decode_torrent_file('torrent-files/ubuntu.iso.torrent')
    info_hash = tracker.get_info_hash(metainfo)

    tracker_response = tracker.send_ths_request(metainfo['announce'], info_hash,
            metainfo['info']['length'])

    peer_info: Dict = tracker_response['peers'][random.randint(0, len(tracker_response['peers']))]

    print('piece length: {}'.format(metainfo['info']['piece length']))
    connection = PeerConnection(peer_info, info_hash, metainfo['info']['piece length'])
    connection.initialize_connection()

    while True:
        read_len = connection.buffer.empty_space()
        recv = connection.socket.recv(4096)
        if len(recv) == 0:
            print('Failed to initialize!')
            connection.set_disconnected()
            sys.exit(1)
        connection.append_to_buffer(recv)
        connection.run_init_states()
        if connection.state != PeerConnection.State.INIT_HANDSHAKE and connection.state != PeerConnection.State.INIT_BITFIELD:
            break

    print('Initialized connection!')
    print(connection.state)

    piece_index = next(i for i in range(1000000) if connection.peer_has_piece(i))
    print('requesting piece {}'.format(42))
    connection.start_piece_download(42)

    while not connection.is_download_completed():
        connection.read_from_socket()
        connection.run_download_state()

    connection.state = PeerConnection.State.IDLE
    downloaded = connection.get_piece_bytes()
    print('download complete: {}'.format(len(downloaded)))


