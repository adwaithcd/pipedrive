# Generated by Django 2.0.2 on 2018-06-04 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0003_auto_20180531_1651'),
    ]

    operations = [
        migrations.AlterField(
            model_name='yellowantredirectstate',
            name='user',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='yellowusertoken',
            name='user',
            field=models.IntegerField(),
        ),
    ]
