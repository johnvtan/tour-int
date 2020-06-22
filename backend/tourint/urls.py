from django.urls import path
from . import views

urlpatterns = [
    path('', views.handle_request_to_base_directory, name='torrents-all'),
    path('<str:file_hash>/', views.handle_request_to_hash)
]
