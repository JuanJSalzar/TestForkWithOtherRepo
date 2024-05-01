# Generated by Django 5.0.4 on 2024-05-01 19:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalApp', '0012_alter_ordermedication_idorder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdiagnosticaid',
            name='idOrder',
            field=models.ForeignKey(db_column='idOrder', on_delete=django.db.models.deletion.CASCADE, related_name='orderDiagnositcAid_Order', to='HospitalApp.order'),
        ),
        migrations.AlterField(
            model_name='orderprocedure',
            name='idOrder',
            field=models.ForeignKey(db_column='idOrder', on_delete=django.db.models.deletion.CASCADE, related_name='orderProcedure_Order', to='HospitalApp.order'),
        ),
    ]
