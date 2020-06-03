from typing import Dict
import requests
import hashlib

import bencode

# TODO actually generate this?
PEER_ID: bytes = bytes([x for x in range(20)])

def decode_torrent_file(filename: str) -> Dict:
    """Opens, reads, and decodes a given torrent file.
    Returns a decoded bencode dict.
    """

    metainfo: Dict = None
    with open(torrent_file, 'rb') as f:
        data = f.read()
        metainfo = bencode.decode(data)

    return metainfo

def send_ths_request(announce_url, info_hash, left, peer_id=PEER_ID, port=6881, up=0, down=0) -> Dict:
    params: Dict = {
        'info_hash': info_hash,
        'peer_id': peer_id,
        'port': port,
        'uploaded': up,
        'downloaded': down,
        'left': left,
    }

    r = requests.get(announce_url, params=params)
    return bencode.decode(r.text.encode('ascii'))

if __name__ == '__main__':
    torrent_file: str = 'charlie-chaplin-avi.torrent'
    metainfo = decode_torrent_file(torrent_file)

    info_hash = hashlib.sha1(bencode.encode(metainfo['info'])).digest()

    response = send_ths_request(metainfo['announce'], info_hash, metainfo['info']['length'])
    print(response)

