# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myTransport', '0005_auto_20180109_0851'),
    ]

    operations = [
        migrations.AddField(
            model_name='action_log',
            name='remote_addr',
            field=models.CharField(default='1.1.1.1', max_length=255),
            preserve_default=False,
        ),
    ]
