from typing import Dict
import socket
import consts
import tracker

HANDSHAKE_SIZE: int = 68

NAME_LENGTH: int = 19
PROTOCOL_NAME: str = 'BitTorrent protocol'
RESERVED_SIZE: int = 8

def create_handshake_bytes(info_hash: bytearray, peer_id: bytearray) -> bytearray:
    assert(len(info_hash) == 20)
    assert(len(peer_id) == 20)

    b: bytearray = bytearray([NAME_LENGTH])
    b.extend(PROTOCOL_NAME.encode('ascii'))
    b.extend(bytearray(RESERVED_SIZE))
    b.extend(info_hash)

    if isinstance(peer_id, bytes):
        b.extend(peer_id)
    elif isinstance(peer_id, str):
        b.extend(peer_id.encode('ascii'))
    elif isinstance(peer_id, int):
        b.extend(peer_id.to_bytes(20))
    else:
        raise ValueError('unknown type of peer_id: {}'.format(type(peer_id)))

    assert(len(b) == HANDSHAKE_SIZE)
    return b

def print_handshake(handshake_bytes: bytearray) -> None:
    name_length: int = handshake_bytes[0]
    protocol_name: str = handshake_bytes[1:name_length+1].decode('ascii')
    print('Handshake name length: {}'.format(name_length))
    print('Handshake protocol name: {}'.format(protocol_name))

if __name__ == '__main__':
    metainfo: Dict = tracker.decode_torrent_file('charlie-chaplin-avi.torrent')
    info_hash = tracker.get_info_hash(metainfo)

    tracker_response = tracker.send_ths_request(metainfo['announce'], info_hash,
            metainfo['info']['length'])

    peer_info: Dict = tracker_response['peers'][0]

    peer_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print('Trying to connect to IP {} on port {}'.format(peer_info['ip'], peer_info['port']))
    peer_socket.connect((peer_info['ip'], peer_info['port']))

    handshake_bytes = create_handshake_bytes(info_hash, peer_info['peer id'])
    peer_socket.send(handshake_bytes)

    received_handshake = peer_socket.recv(HANDSHAKE_SIZE)
    print('Handshake bytes: ', received_handshake)
    print_handshake(received_handshake)
    print('done')


