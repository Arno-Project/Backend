# Generated by Django 3.2.9 on 2022-08-21 16:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0006_alter_systemfeedback_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='systemfeedback',
            options={'ordering': ['-created_at']},
        ),
    ]
