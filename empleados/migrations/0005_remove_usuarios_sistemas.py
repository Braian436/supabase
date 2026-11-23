from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0004_liquidacionessemanales_usuariossistemas_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UsuariosSistemas',
        ),
    ]
