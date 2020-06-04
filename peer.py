from typing import Dict
import socket
import consts
import tracker
import sys
import random

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
        b.extend(peer_id.to_bytes(20, byteorder='big'))
    else:
        raise ValueError('unknown type of peer_id: {}'.format(type(peer_id)))

    assert(len(b) == HANDSHAKE_SIZE)
    print(b)
    return b

def print_handshake(handshake_bytes: bytearray) -> None:
    name_length: int = handshake_bytes[0]
    protocol_name: str = handshake_bytes[1:name_length+1].decode('ascii')
    reserved: bytearray = handshake_bytes[name_length+1:name_length+9]
    info_hash: bytearray = handshake_bytes[name_length+9:name_length+29]
    peer_id: bytearray = handshake_bytes[name_length+29:name_length+49]
    print('Handshake name length: {}'.format(name_length))
    print('Handshake protocol name: {}'.format(protocol_name))
    print('Info hash: {}'.format(info_hash))
    print('Peer id: {}'.format(peer_id))

if __name__ == '__main__':
    metainfo: Dict = tracker.decode_torrent_file('torrent-files/ubuntu.iso.torrent')
    info_hash = tracker.get_info_hash(metainfo)

    tracker_response = tracker.send_ths_request(metainfo['announce'], info_hash,
            metainfo['info']['length'])

    peer_info: Dict = tracker_response['peers'][random.randint(0, len(tracker_response['peers']))]

    peer_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_socket.settimeout(5)
    peer_socket.setblocking(True)

    print('Trying to connect to IP {} on port {}'.format(peer_info['ip'], peer_info['port']))
    print('peer_id: {}'.format(peer_info['peer id']))
    print('info_hash: {}'.format(info_hash))
    try:
        peer_socket.connect((peer_info['ip'], peer_info['port']))
    except Exception as e:
        print('failed to connect: {}'.format(e))
        sys.exit(-1)

    handshake_bytes = create_handshake_bytes(info_hash, consts.PEER_ID)
    print_handshake(handshake_bytes)

    received_handshake = bytearray()
    tries: int = 10
    while len(received_handshake) < HANDSHAKE_SIZE and tries > 0:
        print('Try: {}'.format(11-tries))
        sent = peer_socket.send(bytes(handshake_bytes))
        assert(sent == HANDSHAKE_SIZE)
        received_handshake = peer_socket.recv(HANDSHAKE_SIZE)
        tries -= 1

    print('Handshake bytes: ', received_handshake)
    print_handshake(received_handshake)
    print('done')


