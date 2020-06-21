from django.shortcuts import render
from rest_framework import generics
from .models import Torrents
from .serializers import TorrentsSerializer

# Create your views here.
class ListTorrentsView(generics.ListAPIView):
    queryset = Torrents.objects.all()
    serializer_class = TorrentsSerializer
