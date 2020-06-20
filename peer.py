from typing import Dict, Tuple
import socket
import sys
import random
import enum

import consts
import tracker

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

        message_length = 1 + len(self.payload)
        ret = bytearray()
        ret.extend(message_length.to_bytes(self.MESSAGE_LENGTH_SIZE, byteorder='big'))
        ret.extend(self.id.value.to_bytes(1, byteorder='big'))
        if len(payload):
            ret.extend(self.payload)
        return bytes(ret)

    @classmethod
    def new_request(cls, piece_index, begin, length):
        return cls(cls.Id.REQUEST, payload)

    @classmethod
    def is_valid_message_id(cls, message_id):
        valid_values = [t.value for t in cls.Id]
        return message_id in valid_values

    @classmethod
    def receive_from_socket(cls, peer_socket):
        """Parses a message from the given socket, returns a PeerMessage object"""
        message_length_bytes = read_from_socket_checked(peer_socket, cls.MESSAGE_LENGTH_SIZE)
        message_length = int.from_bytes(message_length_bytes, byteorder='big')

        print('Got message with length {}'.format(message_length))
        if message_length == 0:
            return cls(cls.Id.KEEP_ALIVE, None)

        message_id = read_from_socket_checked(peer_socket, 1)[0]

        if not cls.is_valid_message_id(message_id):
            raise ValueError('Unknown message id {}'.format(message_id))

        print('Got message id {}'.format(cls.Id(message_id)))

        if message_length == 1:
            return cls(cls.Id(message_id), None)

        print('Reading payload...')
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
        print('Requesting block {}'.format(next_block))

        start_byte = next_block * self.BLOCK_SIZE_BYTES
        if start_byte + self.BLOCK_SIZE_BYTES > len(self.piece_bytes):
            length = len(self.piece_bytes) - start_byte
        else:
            length = self.BLOCK_SIZE_BYTES

        ret = PeerMessage.new_request(self.piece_index, self.next_requested_byte, length)
        self.blocks_to_request.remove(next_block)
        return ret 

    def handle_block_response(self, piece_message):
        assert(piece_message.id == PeerMessage.Id.REQUEST)
        piece_index = int.from_bytes(piece_message.payload[0:4], byteorder='big')
        assert(piece_index == self.piece_index)

        start_byte = int.from_bytes(piece_message.payload[4:8], byteorder='big')

        assert(start_byte + len(piece_message.payload) - 8 < len(self.piece_bytes))

        end_byte = start_byte + len(self.piece_bytes)
        self.piece_bytes[start_byte:end_byte] = piece_message.payload[8:]

        received_block = start_byte // self.BLOCK_SIZE_BYTES
        print('Received block {}'.format(received_block))
        self.blocks_received.add(received_block)

    def has_more_blocks(self):
        return len(self.blocks_received) < self.total_num_self.info_hash, blocks 

class PeerConnection:
    """Manages a connection and piece downloads from a peer"""

    # Timeout time in seconds in case a peer fails to connect
    TIMEOUT_S: int = 5
    MAX_QUEUED_REQUESTS: int = 1

    def __init__(self, peer_info: Dict, info_hash: bytearray):
        self.peer_info = peer_info
        self.info_hash = info_hash

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

        return True
    
    def validate_handshake(self, received: bytes) -> bool:
        handshake = PeerHandshake.deserialize(received)
        print('received handshake {}'.format(str(handshake)))
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

        if not self.available_pieces.contains(piece_index):
            raise ValueError('Piece index {} not available'.format(piece_index))

        self.socket.send(PeerMessage(PeerMessage.Id.INTERESTED, None))
        download_state = PieceDownload(piece_index, self.peer_info['piece_length'])

        while download_state.has_more_blocks():
            # We're choked at first, so wait until we receive an unchoke message
            self.receive_message(download_state)
            if self.choked:
                continue
            # send request message and try to download the piece
            for _ in range(num_queued_requests, self.MAX_QUEUED_REQUESTS):
                next_request = download_state.get_next_block_request()
                self.socket.send(next_request.serialize())

        self.socket.send(PeerMessage(PeerMessage.Id.NOT_INTERESTED, None))
        return download_state.piece_bytes 


    def receive_message(self, download_state):
        message = PeerMessage.receive_from_socket(self.socket)

        if message.id == PeerMessage.Id.CHOKE:
            print('Got choked message')
            self.choked = True
        elif message.id == PeerMessage.Id.UNCHOKE:
            print('Got unchoked message')
            self.choked = False
        elif message.id == PeerMessage.Id.INTERESTED:
            print('Got an interested message. what does this mean')
        elif message.id == PeerMessage.Id.NOT_INTERESTED:
            print('Got an uninterested message.')
        elif message.id == PeerMessage.Id.HAVE:
            print('Got have message: new index = {}'.format(new_piece_index))
            assert(message.payload == 4)
            new_piece_index = int.from_bytes(message.payload, byteorder='big')
            self.available_pieces.set(new_piece_index)
        elif message.id == PeerMessage.Id.BITFIELD:
            print('Got bitfield message')
            if self.available_pieces is not None:
                raise ValueError('Error: erroneous bitfield message?')
            self.available_pieces = Bitfield(message.payload)
        elif message.id == PeerMessage.Id.REQUEST:
            print('Got request lol. ignoring')
        elif message.id == PeerMessage.PIECE:
            print('Got a new piece: index = {}, begin = {}, length = {}'.format())
            download_state.handle_block_response(message)



if __name__ == '__main__':
    metainfo: Dict = tracker.decode_torrent_file('torrent-files/ubuntu.iso.torrent')
    info_hash = tracker.get_info_hash(metainfo)

    tracker_response = tracker.send_ths_request(metainfo['announce'], info_hash,
            metainfo['info']['length'])

    peer_info: Dict = tracker_response['peers'][random.randint(0, len(tracker_response['peers']))]
    connection = PeerConnection(peer_info, info_hash)
    if not connection.initialize_connection():
        print('bad could not initialize connection')
