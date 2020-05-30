from typing import Dict
import requests
import bencode

def decode_torrent_file(filename: str) -> Dict:
    """Opens, reads, and decodes a given torrent file.
    Returns a decoded bencode dict.
    """

    metainfo: Dict = None
    with open(torrent_file, 'rb') as f:
        data = f.read()
        metainfo = bencode.decode(data)

    print(metainfo['info']['name'])
    print(metainfo['info']['length'])
    print(metainfo['info']['piece length'])

if __name__ == '__main__':
    torrent_file: str = 'debian-iso.torrent'
    decode_torrent_file(torrent_file)
