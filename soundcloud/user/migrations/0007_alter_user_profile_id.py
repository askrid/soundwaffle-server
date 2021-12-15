# Generated by Django 3.2.6 on 2021-11-26 23:36

from django.db import migrations, models
import user.models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_alter_user_birthday'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_id',
            field=models.CharField(default=user.models.create_permalink, max_length=25, unique=True),
        ),
    ]
