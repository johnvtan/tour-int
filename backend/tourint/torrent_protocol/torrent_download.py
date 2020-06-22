import hashlib
import threading
import os
import pathlib
import queue
from typing import Dict, List

from . import bencode
from . import tracker
from . import peer

TORRENT_OUTPUT_DIRECTORY: str = pathlib.Path(__file__).absolute().parent

def write_piece_to_file(info_hash, piece_idx, piece_bytes, output_directory):
    piece_file_name = '{}_piece_{}.torrent_piece'.format(info_hash.hex(), piece_idx)
    piece_file_path = os.path.join(output_directory, piece_file_name)

    if os.path.exists(piece_file_path):
        print('Failed to write file {} because it already exists'.format(piece_file_path))
        return

    with open(piece_file_path, 'wb+') as f:
        f.write(piece_bytes)


def download_thread_function(peer_connection, download_queue, completed_queue, finished_event,
        output_directory):
    while not finished_event.is_set():
        try:
            piece_idx, piece_hash = download_queue.get(timeout=0.5)
            if not peer_connection.peer_has_piece(piece_idx):
                download_queue.put((piece_idx, piece_hash))
                continue
            
            try:
                piece_bytes = peer_connection.download_piece(piece_idx)
            except Exception as e:
                # if a piece download fails, make sure to return the piece back to the download
                # queue otherwise the download will never finish
                print('peer connection failed {}'.format(e))
                download_queue.put((piece_idx, piece_hash))
                return

            calculated_hash = hashlib.sha1(piece_bytes).digest()
            if calculated_hash != piece_hash:
                download_queue.put((piece_idx, piece_hash))
                continue

            write_piece_to_file(peer_connection.info_hash, piece_idx, piece_bytes, output_directory)
            completed_queue.put(piece_idx)
        except queue.Empty:
            continue


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

    MAX_NUM_CONNECTED_PEERS: int = 20
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

        hashes = PieceHashes(self.info['pieces'])

        pieces_to_download = set(range(len(hashes)))
        num_pieces_downloaded = 0
        total_pieces = len(hashes)
        download_queue = queue.Queue()
        completed_queue = queue.Queue()
        download_finished_event = threading.Event()
        output_directory = TORRENT_OUTPUT_DIRECTORY/("torrent_" + self.info_hash.hex())
        print('Starting download in directory {}'.format(output_directory.as_posix()))

        if os.path.exists(output_directory):
            print('Error: directory already exists, not downloading')
            return
        
        os.makedirs(output_directory.as_posix())

        for i in range(len(hashes)):
            download_queue.put((i, hashes[i]))

        self.peer_connections = self.connect_to_peers(peers, self.info_hash, piece_length)
        assert(len(self.peer_connections) > 0)

        thread_args = [(p, download_queue, completed_queue, download_finished_event,\
            output_directory.as_posix()) for p in self.peer_connections]

        threads = [threading.Thread(target=download_thread_function, args=args) for args in\
                thread_args]

        for i, t in enumerate(threads):
            print('starting thread {}'.format(i))
            t.start()

        while len(pieces_to_download) > 0:
            completed_piece = completed_queue.get()
            pieces_to_download.remove(completed_piece)
            num_pieces_downloaded += 1
            pct = num_pieces_downloaded / total_pieces
            print('Got piece {}. {}% complete'.format(completed_piece, pct))

        download_finished_event.set()

        for t in threads:
            t.join()

        # TODO put all pieces into single file.
        print('Download finished')


if __name__ == '__main__':
    download = TorrentDownload('torrent-files/ubuntu.iso.torrent')
    download.run_download()
