# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-16 10:45
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('course_overviews', '0015_historicalcourseoverview'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimulateCoursePublishConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('arguments', models.TextField(blank=True, default=b'', help_text=b'Useful for manually running a Jenkins job. Specify like "--delay 10 --listeners A B C         --courses X Y Z".')),
                ('changed_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Changed by')),
            ],
            options={
                'verbose_name': 'simulate_publish argument',
            },
        ),
    ]
