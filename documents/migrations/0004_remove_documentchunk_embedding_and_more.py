# Generated by Django 4.2.19 on 2025-03-08 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_alter_documentchunk_embedding_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentchunk',
            name='embedding',
        ),
        migrations.RemoveField(
            model_name='documentchunk',
            name='metadata',
        ),
        migrations.AddField(
            model_name='documentchunk',
            name='embedding_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='documentchunk',
            name='metadata_text',
            field=models.TextField(blank=True, default='{}'),
        ),
    ]
