from django.urls import path
from .views import ListTorrentsView

urlpatterns = [
    path('', ListTorrentsView.as_view(), name='torrents-all')
]
