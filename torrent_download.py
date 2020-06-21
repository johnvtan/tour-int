import bencode
import tracker
import peer
import hashlib
import threading
from typing import Dict, List

class PieceHashes:
    HASH_LENGTH: int = 20
    def __init__(self, piece_hashes):
        self.piece_hashes = piece_hashes 

    def __len__(self):
        return len(self.piece_hashes) // self.HASH_LENGTH

    def __getitem__(self, index):
        start_byte = self.HASH_LENGTH * index
        end_byte = start_byte + self.HASH_LENGTH
        if end_byte > len(self.piece_hashes):
            raise KeyError('end byte {} beyond end of hash bytearray {}'.format(end_byte,
                len(self.piece_hashes)))
        return self.piece_hashes[start_byte:end_byte]

class TorrentDownload:
    """Class that handles downloading a single torrent file.

    Should handle:
    - Contacting peers and requesting/downloading files from peers 
    - All concurrency needed for that stuff
    """

    MAX_NUM_CONNECTED_PEERS: int = 1
    def __init__(self, torrent_file: str):
        self.metainfo: Dict = tracker.decode_torrent_file(torrent_file)
        self.announce_url = self.metainfo['announce']
        self.info = self.metainfo['info']

        self.info_hash = hashlib.sha1(bencode.encode(self.info)).digest() 

        self.peer_connections = []

    def contact_tracker(self):
        return tracker.send_ths_request(self.announce_url, self.info_hash, self.info['length'])

    @classmethod
    def connect_to_peers(cls, peers, info_hash, piece_length) -> List[peer.PeerConnection]:
        connected = []
        # TODO will this be slow when I have a lot/will I need to thread this too?
        # I might be dropped if I try to wait for all connections
        for peer_info in peers:
            if len(connected) >= cls.MAX_NUM_CONNECTED_PEERS:
                break

            peer_connection = peer.PeerConnection(peer_info, info_hash, piece_length) 

            try:
                init_ret = peer_connection.initialize_connection()
                if init_ret:
                    connected.append(peer_connection)
            except Exception as e:
                print('Failed to connect to peer {} because {}'.format(str(peer_connection), e))

        return connected

    def run_download(self):
        tracker_response = self.contact_tracker()
        peers = tracker_response['peers']
        piece_length = self.info['piece length']

        self.peer_connections = self.connect_to_peers(peers, self.info_hash, piece_length)
        assert(len(self.peer_connections) > 0)
        hashes = PieceHashes(self.info['pieces'])

        pieces_to_download = set(range(len(hashes)))
        p = self.peer_connections[0]
        for piece_idx in iter(pieces_to_download):
            if p.peer_has_piece(piece_idx):
                print('===================Downloading piece {}==============='.format(piece_idx))
                piece_bytes = p.download_piece(piece_idx)
                piece_hash = hashlib.sha1(piece_bytes).digest()
                assert(piece_hash == hashes[piece_idx])
                print('======Successful hash match on piece download==================')
        print('Done')

if __name__ == '__main__':
    download = TorrentDownload('torrent-files/ubuntu.iso.torrent')
    download.run_download()
