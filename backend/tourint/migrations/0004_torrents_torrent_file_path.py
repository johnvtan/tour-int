# Generated by Django 3.0.8 on 2020-07-11 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tourint', '0003_torrents_download_directory'),
    ]

    operations = [
        migrations.AddField(
            model_name='torrents',
            name='torrent_file_path',
            field=models.TextField(default='torrentfilepath'),
        ),
    ]
