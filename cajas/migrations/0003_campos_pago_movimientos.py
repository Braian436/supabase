from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cajas', '0002_movimientoscajas_delete_movimientoscaja'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE movimientos_cajas "
                "ADD COLUMN IF NOT EXISTS metodo_pago varchar(20) NOT NULL DEFAULT 'efectivo', "
                "ADD COLUMN IF NOT EXISTS monto_recibido numeric(12,2), "
                "ADD COLUMN IF NOT EXISTS vuelto numeric(12,2);"
            ),
            reverse_sql=(
                "ALTER TABLE movimientos_cajas "
                "DROP COLUMN IF EXISTS vuelto, "
                "DROP COLUMN IF EXISTS monto_recibido, "
                "DROP COLUMN IF EXISTS metodo_pago;"
            ),
        ),
    ]
