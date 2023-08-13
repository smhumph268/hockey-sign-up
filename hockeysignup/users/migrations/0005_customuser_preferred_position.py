# Generated by Django 4.1.6 on 2023-07-30 01:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_customuser_skill_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='preferred_position',
            field=models.CharField(choices=[('d', 'D'), ('c', 'C'), ('b', 'B')], default='forward', max_length=7),
        ),
    ]
