from typing import Dict
import requests
import hashlib

from . import consts
from . import bencode


def decode_torrent_file(filename: str) -> Dict:
    """Opens, reads, and decodes a given torrent file.
    Returns a decoded bencode dict.
    """

    metainfo: Dict = None
    with open(filename, 'rb') as f:
        data = f.read()
        metainfo = bencode.decode(data)

    return metainfo

def send_ths_request(announce_url, info_hash, left, peer_id=consts.PEER_ID,
                     port=consts.DEFAULT_PORT, up=0, down=0) -> Dict:
    """Peers should send this request regularly, based on the 'interval' field that is sent in the
    response.
    """
    params: Dict = {
        'info_hash': info_hash,
        'peer_id': peer_id,
        'port': port,
        'uploaded': up,
        'downloaded': down,
        'left': left,
    }

    r = requests.get(announce_url, params=params)
    return bencode.decode(r.content)

def get_info_hash(metainfo: Dict) -> bytearray:
    return hashlib.sha1(bencode.encode(metainfo['info'])).digest()

if __name__ == '__main__':
    torrent_file: str = 'torrent-files/ubuntu.iso.torrent'
    metainfo = decode_torrent_file(torrent_file)

    info_hash = get_info_hash(metainfo)

    response = send_ths_request(metainfo['announce'], info_hash, metainfo['info']['length'])
    print(response)

