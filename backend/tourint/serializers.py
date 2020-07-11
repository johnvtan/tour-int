from rest_framework import serializers
from .models import Torrents

class TorrentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Torrents
        fields = (
            'name',
            'file_hash',
            'torrent_file_path',
            'total_size_bytes',
            'downloaded_bytes',
            'download_status',
            'number_of_seeders',
            'number_of_peers_connected',
        )
