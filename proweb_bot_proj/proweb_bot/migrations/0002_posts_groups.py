# Generated by Django 5.1.2 on 2024-10-16 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proweb_bot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='posts',
            name='groups',
            field=models.ManyToManyField(blank=True, null=True, to='proweb_bot.groups', verbose_name='Группы'),
        ),
    ]
