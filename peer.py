from typing import Dict, Tuple
from queue import Queue
import socket
import sys
import random
import enum

import consts
import tracker
import time
import hashlib

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

    MESSAGE_LENGTH_SIZE: int = 4
    def __init__(self, message_id, payload=None):
        self.id = message_id 
        self.payload = payload

    def __str__(self):
        return 'PeerMessage {}, payload = {}'.format(self.id, self.payload)

    def serialize(self) -> bytes:
        if self.id == self.Id.KEEP_ALIVE:
            return bytearray(MESSAGE_LENGTH_SIZE)

        message_length = 1 if not self.payload else 1 + len(self.payload) 
        ret = bytearray()
        ret.extend(message_length.to_bytes(self.MESSAGE_LENGTH_SIZE, byteorder='big'))
        ret.extend(self.id.value.to_bytes(1, byteorder='big'))
        if self.payload is not None and len(self.payload) > 0:
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
    def is_valid_message_id(cls, message_id):
        valid_values = [t.value for t in cls.Id]
        return message_id in valid_values

    @classmethod
    def receive_from_socket(cls, peer_socket):
        """Parses a message from the given socket, returns a PeerMessage object"""
        message_length_bytes = read_from_socket_checked(peer_socket, cls.MESSAGE_LENGTH_SIZE)
        message_length = int.from_bytes(message_length_bytes, byteorder='big')

        if message_length == 0:
            return cls(cls.Id.KEEP_ALIVE, None)

        message_id = read_from_socket_checked(peer_socket, 1)[0]

        if not cls.is_valid_message_id(message_id):
            raise ValueError('Unknown message id {}'.format(message_id))

        if message_length == 1:
            return cls(cls.Id(message_id), None)

        payload_length = message_length - 1
        payload_bytes = read_from_socket_checked(peer_socket, payload_length)
        return cls(cls.Id(message_id), payload_bytes)

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

    def handle_block_response(self, piece_message):
        assert(piece_message.id == PeerMessage.Id.PIECE)
        piece_index = int.from_bytes(piece_message.payload[0:4], byteorder='big')
        assert(piece_index == self.piece_index)

        start_byte = int.from_bytes(piece_message.payload[4:8], byteorder='big')

        end_byte = start_byte + len(piece_message.payload[8:])

        if end_byte > len(self.piece_bytes):
            raise ValueError('End byte too large: got {}, max: {}'.format(end_byte,
                len(self.piece_bytes)))

        self.piece_bytes[start_byte:end_byte] = piece_message.payload[8:]

        received_block = start_byte // self.BLOCK_SIZE_BYTES
        self.blocks_received.add(received_block)

    def all_blocks_received(self):
        return len(self.blocks_received) == self.total_num_blocks

    def has_more_blocks_to_request(self):
        return len(self.blocks_to_request) > 0 

class PeerConnection:
    """Manages a connection and piece downloads from a peer"""

    # Timeout time in seconds in case a peer fails to connect
    TIMEOUT_S: int = 5
    MAX_QUEUED_REQUESTS: int = 10

    def __init__(self, peer_info: Dict, info_hash: bytearray, piece_length):
        self.peer_info = peer_info
        self.info_hash = info_hash
        self.piece_length = piece_length

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.TIMEOUT_S)
        self.choked = True

        self.peer_id = None

        self.num_queued_requests = 0

        self.available_pieces = None

    def __str__(self):
        return "PeerConnection on IP = {}:{} for hash {}".format(self.peer_info['ip'],
                self.peer_info['port'], self.info_hash)

    def initialize_connection(self) -> bool:
        """
        By the end of this function, we should know whether or not we can start downloading from a
        peer.
        """
        # TODO how to track state of connection if this fails?
        print('initializing connection')
        self.socket.connect((self.peer_info['ip'], self.peer_info['port']))

        handshake = PeerHandshake(consts.PEER_ID, self.info_hash)

        print("Sent handshake {}".format(str(handshake)))
        self.socket.send(handshake.serialize())

        received_handshake = self.socket.recv(PeerHandshake.HANDSHAKE_SIZE)
        if not self.validate_handshake(received_handshake):
            print("Bad handshake")
            return False

        # receive one message, hope it is bitfield message
        self.receive_message(None)
        if self.available_pieces is None:
            print('Did not receive a bitfield message on initialization, failed')
            return False

        self.socket.settimeout(10)
        return True
    
    def validate_handshake(self, received: bytes) -> bool:
        handshake = PeerHandshake.deserialize(received)
        if handshake.info_hash != self.info_hash:
            print('mismatching info hash in handshake: got {}, expected\
                    {}'.format(handshake.info_hash, self.info_hash))
            return False
        
        self.peer_id = handshake.peer_id
        return True
    
    def download_piece(self, piece_index):
        """Runs loop to download a full piece from the peer.

        Assumes that a valid bitfield has been received
        """
        # TODO send interested?

        assert(self.peer_has_piece(piece_index))

        self.socket.send(PeerMessage(PeerMessage.Id.INTERESTED, None).serialize())
        download_state = PieceDownload(piece_index, self.piece_length)

        # in case we aren't choked, send some requests to start
        self.send_block_requests(download_state)
        while not download_state.all_blocks_received():
            # We're choked at first, so wait until we receive an unchoke message
            self.receive_message(download_state)
            self.send_block_requests(download_state)

        self.socket.send(PeerMessage(PeerMessage.Id.NOT_INTERESTED, None).serialize())
        return download_state.piece_bytes 

    def send_block_requests(self, download_state):
        if self.choked:
            time.sleep(0.01)
            return
        
        for _ in range(self.num_queued_requests, self.MAX_QUEUED_REQUESTS):
            if not download_state.has_more_blocks_to_request():
                break
            next_request = download_state.get_next_block_request()
            self.socket.send(next_request.serialize())
            self.num_queued_requests += 1
    
    def peer_has_piece(self, index):
        if not self.available_pieces:
            raise ValueError('Bitfield not initialized')
        return self.available_pieces.contains(index)

    def receive_message(self, download_state):
        message = PeerMessage.receive_from_socket(self.socket)

        if message.id == PeerMessage.Id.CHOKE:
            print('Thread choked')
            self.choked = True
        elif message.id == PeerMessage.Id.UNCHOKE:
            print('Thread unchoked')
            self.choked = False
        elif message.id == PeerMessage.Id.INTERESTED:
            pass
        elif message.id == PeerMessage.Id.NOT_INTERESTED:
            pass
        elif message.id == PeerMessage.Id.HAVE:
            assert(len(message.payload) == 4)
            new_piece_index = int.from_bytes(message.payload, byteorder='big')
            self.available_pieces.set(new_piece_index)
        elif message.id == PeerMessage.Id.BITFIELD:
            if self.available_pieces is not None:
                raise ValueError('Error: erroneous bitfield message?')
            self.available_pieces = Bitfield(message.payload)
        elif message.id == PeerMessage.Id.REQUEST:
            pass
        elif message.id == PeerMessage.Id.PIECE:
            download_state.handle_block_response(message)
            self.num_queued_requests -= 1

if __name__ == '__main__':
    metainfo: Dict = tracker.decode_torrent_file('torrent-files/ubuntu.iso.torrent')
    info_hash = tracker.get_info_hash(metainfo)

    tracker_response = tracker.send_ths_request(metainfo['announce'], info_hash,
            metainfo['info']['length'])

    peer_info: Dict = tracker_response['peers'][random.randint(0, len(tracker_response['peers']))]

    print('piece length: {}'.format(metainfo['info']['piece length']))
    connection = PeerConnection(peer_info, info_hash, metainfo['info']['piece length'])
    if not connection.initialize_connection():
        print('bad could not initialize connection')
        sys.exit(1)

    for i in range(100000):
        if connection.peer_has_piece(i):
            print('REQUESTING PIECE {}'.format(i))
            piece_bytes = connection.download_piece(i)
            break

