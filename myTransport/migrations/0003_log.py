# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myTransport', '0002_usertoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.IntegerField(help_text=b'0\xe8\xa1\xa8\xe7\xa4\xba\xe4\xb8\x8a\xe4\xbc\xa0\xef\xbc\x8c1\xe8\xa1\xa8\xe7\xa4\xba\xe4\xb8\x8b\xe8\xbd\xbd', choices=[(0, b'upload'), (1, b'download')])),
                ('file', models.TextField(null=True, blank=True)),
                ('file_size', models.CharField(max_length=255)),
                ('ops_time', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
