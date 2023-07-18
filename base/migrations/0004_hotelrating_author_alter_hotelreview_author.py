# Generated by Django 4.2.2 on 2023-06-24 09:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0003_merge_20230624_1147'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotelrating',
            name='author',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='hotelratings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='hotelreview',
            name='author',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='hotelreviews', to=settings.AUTH_USER_MODEL),
        ),
    ]