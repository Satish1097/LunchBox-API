# Generated by Django 5.1.1 on 2024-10-14 08:02

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authapp', '0012_alter_subscription_start_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionDetail',
            fields=[
                ('Transaction_id', models.CharField(default=uuid.uuid4, editable=False, max_length=100, primary_key=True, serialize=False)),
                ('Payment_id', models.CharField(max_length=100, null=True, unique=True)),
                ('transaction_amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('payment_status', models.CharField(choices=[('Success', 'Success'), ('Failed', 'Failed'), ('Pending', 'Pending')], default='Pending', max_length=10)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='authapp.child')),
                ('order_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='authapp.order')),
                ('subscription_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='authapp.subscription')),
            ],
        ),
    ]
