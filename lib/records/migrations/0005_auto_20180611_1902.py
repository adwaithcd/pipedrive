# Generated by Django 2.0.2 on 2018-06-11 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0004_auto_20180604_1845'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='yellowusertoken',
            name='webhook_id',
        ),
        migrations.AddField(
            model_name='pipedriveusertoken',
            name='webhook_id',
            field=models.CharField(default='', max_length=256),
        ),
    ]