# Generated by Django 4.2.2 on 2023-06-24 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0005_rename_hotel_roomfeature_room"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hotelreview",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="hotelreview",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]