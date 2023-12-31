# Generated by Django 4.2.2 on 2023-07-03 11:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_alter_booking_special_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='room',
            field=models.OneToOneField(on_delete=django.db.models.deletion.RESTRICT, related_name='bookings', to='base.room'),
        ),
        migrations.AlterField(
            model_name='hotel',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
