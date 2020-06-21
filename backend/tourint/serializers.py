from rest_framework import serializers
from .models import Torrents

class TorrentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Torrents
        fields = ("name")
