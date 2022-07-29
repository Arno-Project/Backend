# Generated by Django 3.2.9 on 2022-07-17 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20220716_0210'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialist',
            name='is_validated',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
