from django.db import models

# Create your models here.
class Torrents(models.Model):

    class DownloadStatus(models.TextChoices):
        COMPLETED = 'Completed'
        IN_PROGRESS = 'In Progress'
        PAUSED = 'Paused'
        CANCELLED = 'Cancelled'

    # filename
    name = models.CharField(max_length=255, default="name")

    # Hash of the torrent as a hex string
    file_hash = models.CharField(max_length=255, default="default")

    total_size_bytes = models.BigIntegerField(default=0)
    downloaded_bytes = models.BigIntegerField(default=0)

    download_status = models.CharField(
        max_length=15,
        choices=DownloadStatus.choices,
        default=DownloadStatus.IN_PROGRESS
    )

    number_of_seeders = models.PositiveIntegerField(default=0)
    number_of_peers_connected = models.PositiveIntegerField(default=0)

    download_directory = models.CharField(max_length=255, default="./downloads/")

    def __str__(self):
        return "Torrent {}, hash = {}, status = {}, total size = {} bytes, downloaded = {} bytes".format(
                    self.name, self.file_hash, self.download_status, self.total_size_bytes,
                    self.downloaded_bytes
                )
