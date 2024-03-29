# Generated by Django 3.2.9 on 2022-08-02 19:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0003_auto_20220718_0014'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField()),
                ('type', models.CharField(choices=[('S', 'System'), ('U', 'User')], max_length=1)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='accounts.normaluser')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='send_messages', to='accounts.normaluser')),
            ],
        ),
    ]
