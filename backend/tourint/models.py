from django.db import models

# Create your models here.
class Torrents(models.Model):
    # filename
    name = models.CharField(max_length=255, null=False)
    def __str__(self):
        return "Torrents {}".format(self.name)
