from rest_framework.permissions import BasePermission, SAFE_METHODS


def _tiene_grupo(usuario, grupo):
    if not usuario or not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    return usuario.groups.filter(name=grupo).exists()


class TieneGrupo(BasePermission):
    """Permite el acceso solo a usuarios autenticados de un grupo puntual."""

    grupo = ''

    def has_permission(self, request, view):
        return _tiene_grupo(request.user, self.grupo)


class EsAdministrador(TieneGrupo):
    grupo = 'Administrador'


class EsBarbero(TieneGrupo):
    grupo = 'Barbero'


class EsCajero(TieneGrupo):
    grupo = 'Cajero'


class EsBarberoOAdministrador(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return _tiene_grupo(usuario, 'Barbero') or _tiene_grupo(
            usuario, 'Administrador'
        )


class AdministradorOLectura(BasePermission):
    """Lectura pública; escritura reservada al Administrador."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return _tiene_grupo(request.user, 'Administrador')
