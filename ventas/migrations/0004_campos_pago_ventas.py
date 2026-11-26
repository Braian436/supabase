from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0003_ventas_delete_ordenes_delete_pagosordenes'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE ventas "
                "ADD COLUMN IF NOT EXISTS metodo_pago varchar(20), "
                "ADD COLUMN IF NOT EXISTS monto_recibido numeric(12,2), "
                "ADD COLUMN IF NOT EXISTS vuelto numeric(12,2);"
            ),
            reverse_sql=(
                "ALTER TABLE ventas "
                "DROP COLUMN IF EXISTS vuelto, "
                "DROP COLUMN IF EXISTS monto_recibido, "
                "DROP COLUMN IF EXISTS metodo_pago;"
            ),
        ),
    ]
