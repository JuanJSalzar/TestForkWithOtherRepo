# Generated by Django 5.0.4 on 2024-05-03 20:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalApp', '0020_alter_ordermedication_item_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visit',
            name='orderMedication',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orderMedication', to='HospitalApp.order'),
        ),
    ]
