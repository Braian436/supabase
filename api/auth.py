from django.contrib.auth import authenticate
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from empleados.models import Empleados


def grupo_principal(usuario):
    """Devuelve el nombre del grupo de auth del usuario (rol laboral)."""
    if not usuario:
        return ''
    if usuario.is_superuser:
        return 'Administrador'
    grupo = usuario.groups.first()
    return grupo.name if grupo else ''


def empleado_de_usuario(usuario):
    """Resuelve el empleado vinculado a un usuario de auth."""
    if not usuario:
        return None
    return Empleados.objects.filter(id_user=usuario).first()


def datos_sesion(usuario, token=None):
    empleado = empleado_de_usuario(usuario)
    nombre = usuario.get_full_name() or usuario.get_username()
    if empleado is not None:
        nombre = f'{empleado.nombre} {empleado.apellido}'.strip() or nombre
    datos = {
        'usuario': usuario.get_username(),
        'nombre': nombre,
        'rol': grupo_principal(usuario),
        'id_empleado': empleado.pk if empleado else None,
        'id_user': usuario.pk,
    }
    if token is not None:
        datos['token'] = token
    return datos


class LoginSerializer(serializers.Serializer):
    usuario = serializers.CharField(allow_blank=False, trim_whitespace=True)
    contrasena = serializers.CharField(allow_blank=False, trim_whitespace=False)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario = authenticate(
            request,
            username=serializer.validated_data['usuario'],
            password=serializer.validated_data['contrasena'],
        )
        if usuario is None:
            return Response(
                {'detail': 'Usuario o contraseña incorrectos.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        rol = grupo_principal(usuario)
        if not rol:
            return Response(
                {'detail': 'La cuenta no tiene un rol asignado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=usuario)
        return Response(datos_sesion(usuario, token=token.key))


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(datos_sesion(request.user))
