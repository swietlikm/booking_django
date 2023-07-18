# Generated by Django 4.2.2 on 2023-07-13 18:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0014_remove_booking_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="status",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="bookingstatuses",
                to="base.bookingstatus",
            ),
        ),
    ]
