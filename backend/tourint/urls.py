from django.urls import path
from .views import ListTorrentsView

urlpatterns = [
    path('torrents/', ListTorrentsView.as_view(), name='torrents-all')
]
