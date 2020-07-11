import hashlib
import threading
import os
import pathlib
import queue
import select
import random
from multiprocessing import Process
from collections import deque
from typing import Dict, List

# TODO python imports suck
if __package__ is None or __package__ == '':
    # This means I'm running the script directly which means I can't use relative imports
    import bencode
    import tracker
    import peer
else:
    from . import bencode
    from . import tracker
    from . import peer

TORRENT_OUTPUT_DIRECTORY: str = pathlib.Path(__file__).absolute().parent
TORRENT_PIECE_ENDING: str = 'torrent_piece'

def write_piece_to_file(info_hash, piece_idx, piece_bytes, output_directory):
    piece_file_name = '{}_piece_{}.{}'.format(info_hash.hex(), piece_idx, TORRENT_PIECE_ENDING)
    piece_file_path = os.path.join(output_directory, piece_file_name)

    if os.path.exists(piece_file_path):
        print('Failed to write file {} because it already exists'.format(piece_file_path))
        return

    with open(piece_file_path, 'wb+') as f:
        f.write(piece_bytes)

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

class TorrentDownload(Process):
    """Class that handles downloading a single torrent file.

    Should handle:
    - Contacting peers and requesting/downloading files from peers 
    - All concurrency needed for that stuff
    """

    MAX_NUM_CONNECTED_PEERS: int = 5 
    def __init__(self, torrent_file: str, db_entry):
        Process.__init__(self)
        self.metainfo: Dict = tracker.decode_torrent_file(torrent_file)
        self.announce_url = self.metainfo['announce']
        self.info = self.metainfo['info']

        self.hashes = PieceHashes(self.info['pieces'])

        self.info_hash = hashlib.sha1(bencode.encode(self.info)).digest() 

        self.output_directory = TORRENT_OUTPUT_DIRECTORY/("torrent_" + self.info_hash.hex())

        self.poll_object = None

        # maps from socket fd to peer connection object
        self.peer_connections = {}

        self.pieces_to_download = set([i for i in range(len(self.hashes))])
        self.completed_pieces = set()
        self.num_dc = 0

        self.db_entry = db_entry
        self.db_entry.save()

    def contact_tracker(self):
        return tracker.send_ths_request(self.announce_url, self.info_hash, self.info['length'])

    def setup_output_directory(self):
        print('Starting download in directory {}'.format(self.output_directory.as_posix()))

        if os.path.exists(self.output_directory):
            print('Directory already exists, collecting all downloaded pieces...')
            existing_piece_files = [f for f in os.listdir(self.output_directory) if
                    f.endswith(TORRENT_PIECE_ENDING)]
            for piece_file in existing_piece_files:
                name = piece_file.split('.')[0]
                split_name = name.split('_')
                piece_index = int(split_name[2])
                self.pieces_to_download.remove(piece_index)
                self.completed_pieces.add(piece_index)
        else:
            print('Starting new download')
            os.makedirs(self.output_directory.as_posix())
    
    def combine_piece_files(self):
        pass

    def run(self):
        self.setup_output_directory()
        self.initialize()
        self.run_download()

    def initialize(self):
        tracker_response = self.contact_tracker()
        peer_info_list = tracker_response['peers']
        self.db_entry.number_of_seeders = len(peer_info_list)

        read_only_flags = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
        self.poll_object = select.poll()
        for peer_info in peer_info_list:
            peer_connection = peer.PeerConnection(peer_info, self.info_hash)
            try:
                peer_connection.initialize_connection()
            except Exception as e:
                print('Could not connect: {}'.format(e))
                continue
            self.peer_connections[peer_connection.socket.fileno()] = peer_connection
            self.poll_object.register(peer_connection.socket, read_only_flags)

        print('initialized {} connections'.format(len(self.peer_connections)))
        self.db_entry.number_of_peers_connected = len(self.peer_connections)
        self.db_entry.save()

    def handle_poll_event_for_peer(self, peer_connection, event):
        if event == select.POLLHUP or event == select.POLLRDHUP:
            self.num_dc += 1
            print('{} disconnected: {}'.format(str(peer_connection), self.num_dc))
            peer_connection.set_disconnected()
            self.replace_disconnected_piece_index(peer_connection)
            self.poll_object.unregister(peer_connection.socket.fileno())
        elif event == select.POLLIN:
            peer_connection.read_from_socket()
            peer_connection.run_state_machine()
        elif event == select.POLLERR:
            print('peer had error??')
        elif event == select.POLLNVAL:
            #print('peer {} invalid??'.format(peer_connection))
            pass

    def in_end_game(self):
        idle_peers = [p for p in self.peer_connections.values() if p.is_idle()]

        return len(idle_peers) >= len(self.pieces_to_download)
    
    def stop_download(self, cancelled_piece_index=None):
        for p in self.peer_connections.values():
            if not cancelled_piece_index or cancelled_piece_index == p.get_current_piece_index():
                p.cancel_piece_download()

    def replace_disconnected_piece_index(self, peer):
        assert(peer.is_disconnected())
        unfinished_piece = peer.get_current_piece_index()
        if unfinished_piece >= 0:
            self.pieces_to_download.add(unfinished_piece)

    def get_piece_size(self, piece_index):
        if piece_index == len(self.hashes) - 1:
            # This is the last piece, so might be smaller than the piece length
            return self.info['length'] % self.info['piece length']
        return self.info['piece length']
    
    def run_download(self):
        print('Download starting...')
        while len(self.completed_pieces) < len(self.hashes):
            for fd, event in self.poll_object.poll():
                peer_connection = self.peer_connections[fd]
                self.handle_poll_event_for_peer(peer_connection, event)

                if peer_connection.is_disconnected():
                    peer_connection.set_disconnected()
                    self.replace_disconnected_piece_index(peer_connection)
                    self.poll_object.unregister(fd)
                elif peer_connection.is_download_completed():
                    completed_piece_index = peer_connection.get_current_piece_index()
                    piece_bytes = peer_connection.get_piece_bytes()
                    piece_hash = self.hashes[completed_piece_index]
                    calculated_hash = hashlib.sha1(piece_bytes).digest()
                    if piece_hash != calculated_hash:
                        print('Bad hash! c: {} vs r: {}'.format(calculated_hash, piece_hash))
                        self.pieces_to_download.add(completed_piece_index)
                    else:
                        self.completed_pieces.add(completed_piece_index)
                        write_piece_to_file(self.info_hash, completed_piece_index, piece_bytes,
                                self.output_directory)

                        if self.in_end_game():
                            self.stop_download(completed_piece_index)
                            if completed_piece_index in self.pieces_to_download:
                                self.pieces_to_download.remove(completed_piece_index)

                        pct_complete = len(self.completed_pieces) / len(self.hashes) * 100
                        print('Got {} / {} pieces. {}% complete'
                               .format(len(self.completed_pieces), len(self.hashes), pct_complete),
                               end='\r')
                        self.db_entry.downloaded_bytes = len(self.completed_pieces) * self.info['piece length']
                        self.db_entry.save()

                if self.in_end_game():
                    # This might not be exactly the situation that the spec says is the 'end game'
                    # but whatever

                    # blast all idle peers with the next not downloaded piece 
                    if len(self.pieces_to_download) > 0:
                        next_piece = next(iter(self.pieces_to_download))
                    else:
                        # In case any peers are still connected but have been choked for a long
                        # time, if we run out of pieces in pieces_to_download, start downloading
                        # pieces that are being actively downloaded and let all the connections
                        # race.
                        try:
                            next_piece = next(p.get_current_piece_index() for p in\
                                self.peer_connections.values() if p.is_downloading())
                        except StopIteration:
                            # This means we're done, I think
                            continue

                    idle_peers = [p for p in self.peer_connections.values() if p.is_idle() and\
                            not p.choked]

                    for p in idle_peers:
                        p.start_piece_download(next_piece, self.get_piece_size(next_piece))

                elif peer_connection.is_idle() and len(self.pieces_to_download) > 0:
                    next_piece = random.sample(self.pieces_to_download, 1)[0]
                    self.pieces_to_download.remove(next_piece)
                    peer_connection.start_piece_download(next_piece, self.get_piece_size(next_piece))


        print('\n')
        print('Done!')
        for p in self.peer_connections.values():
            p.set_disconnected()
           

if __name__ == '__main__':
    download = TorrentDownload('torrent-files/ubuntu.iso.torrent')
    download.setup_output_directory()
    download.initialize()
    download.run_download()
