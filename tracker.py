from typing import Dict
import requests
import bencode

def decode_torrent_file(filename: str) -> Dict:
    """Opens, reads, and decodes a given torrent file.
    Returns a decoded bencode dict.
    """

    with open(torrent_file, 'rb') as f:
        data = f.read()
        data = bencode.decode(data)
        print(data)

if __name__ == '__main__':
    torrent_file: str = 'debian-iso.torrent'
    decode_torrent_file(torrent_file)
