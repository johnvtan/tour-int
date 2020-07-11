from django.shortcuts import render
from rest_framework import generics
from django.http import HttpRequest, HttpResponse
from .models import Torrents
from .serializers import TorrentsSerializer

from .torrent_protocol import tracker
from .torrent_protocol import bencode

import os
import urllib
import json

DOWNLOAD_FOLDER: str = './downloads/'
TORRENT_FILE_ENDING: str = '.torrent'

# Create your views here.
class ListTorrentsView(generics.ListAPIView):
    queryset = Torrents.objects.all()
    serializer_class = TorrentsSerializer

def handle_request_to_base_directory(request):
    if request.method == 'GET':
        return ListTorrentsView.as_view()(request)
    elif request.method == 'POST':
        if not os.path.exists(DOWNLOAD_FOLDER):
            os.makedirs(DOWNLOAD_FOLDER)

        request_body_string = request.body.decode('utf-8')
        request_json = json.loads(request_body_string)
        url = request_json['torrent']['url']
        with urllib.request.urlopen(url) as f:
            data_from_url = f.read()
            metainfo = bencode.decode(data_from_url)
            info_hash = tracker.get_info_hash(metainfo)

            torrent_file_name = metainfo['info']['name']\
                + '_' + info_hash.hex() + TORRENT_FILE_ENDING

            torrent_file_path = os.path.join(DOWNLOAD_FOLDER, torrent_file_name)
            with open(torrent_file_path, 'wb+') as torrent_file:
                torrent_file.write(data_from_url)

        t = Torrents(name = metainfo['info']['name'],
                     file_hash = info_hash.hex(),
                     torrent_file_path = torrent_file_path,
                     total_size_bytes = metainfo['info']['length'],
                     downloaded_bytes = 0,
                     download_status = Torrents.DownloadStatus.IN_PROGRESS,
                     number_of_seeders = 0,
                     number_of_peers_connected = 0,
                     download_directory = DOWNLOAD_FOLDER)
        t.save()
        return HttpResponse(status=200)

def handle_request_to_hash(request, file_hash):
    if request.method == 'GET':
        print('Got GET request for file hash {}'.format(file_hash))
        metainfo = tracker.decode_torrent_file('/home/john/dev/tour-int/backend/tourint/torrent_protocol/torrent-files/ubuntu.iso.torrent')
        print('test: {}'.format(metainfo['announce']))
        return HttpResponse(status=200)
    elif request.method == 'POST':
        print('Got POST request for file hash {}'.format(file_hash))
        return HttpResponse(status=200)
