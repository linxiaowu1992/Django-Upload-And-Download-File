# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myTransport', '0004_auto_20180109_0824'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='action_log',
            table='action_log',
        ),
    ]
