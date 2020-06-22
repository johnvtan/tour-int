from django.shortcuts import render
from rest_framework import generics
from django.http import HttpRequest, HttpResponse
from .models import Torrents
from .serializers import TorrentsSerializer

# Create your views here.
class ListTorrentsView(generics.ListAPIView):
    queryset = Torrents.objects.all()
    serializer_class = TorrentsSerializer

def handle_request_to_base_directory(request):
    if request.method == 'GET':
        return ListTorrentsView.as_view()(request)
    elif request.method == 'POST':
        print('Got post to base directory')
        return HttpResponse(status=200)

def handle_request_to_hash(request, file_hash):
    if request.method == 'GET':
        print('Got GET request for file hash {}'.format(file_hash))
        return HttpResponse(status=200)
    elif request.method == 'POST':
        print('Got POST request for file hash {}'.format(file_hash))
        return HttpResponse(status=200)
