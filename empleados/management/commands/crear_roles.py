from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


APPS_PROYECTO = (
    'turnos', 'ventas', 'cajas', 'productos', 'compras', 'empleados', 'servicios'
)


def _permisos(modelos, acciones):
    return [f'{accion}_{modelo}' for modelo in modelos for accion in acciones]


ROLES = {
    'Administrador': None,
    'Cajero': _permisos(
        (
            'clientes', 'turnos', 'turnosexpress', 'servicios', 'serviciosturnos',
            'ventas', 'detallesproductos', 'detallesservicios', 'cajas',
            'movimientoscajas',
        ),
        ('view', 'add', 'change'),
    ) + _permisos(
        ('productos', 'marcas', 'categorias', 'descuentos'),
        ('view',),
    ),
    'Barbero': _permisos(
        ('turnos', 'turnosexpress'),
        ('view', 'add'),
    ) + _permisos(
        ('servicios', 'serviciosturnos', 'liquidacionessemanales'),
        ('view',),
    ),
}


class Command(BaseCommand):
    help = 'Crea los grupos (roles) del sistema y les asigna sus permisos'

    def handle(self, *args, **options):
        for nombre, codenames in ROLES.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            if nombre == 'Administrador':
                anterior = Group.objects.filter(name='Dueño').first()
                if anterior:
                    grupo.user_set.add(*anterior.user_set.all())
                    anterior.delete()

            permisos = Permission.objects.filter(
                content_type__app_label__in=APPS_PROYECTO
            )
            if codenames is not None:
                permisos = permisos.filter(codename__in=codenames)
            grupo.permissions.set(permisos)
            self.stdout.write(f'{nombre}: {permisos.count()} permisos asignados')
