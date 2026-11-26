from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0006_empleadocuenta'),
    ]

    operations = [
        # Retire the ORM state without dropping legacy tables or their data.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='Roles'),
                migrations.DeleteModel(name='EmpleadoCuenta'),
            ],
        ),
    ]
