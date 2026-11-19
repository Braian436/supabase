from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'

    def parse_rate(self, rate):
        requests, period = rate.split('/')
        if period == '15m':
            return int(requests), 15 * 60
        return super().parse_rate(rate)


class TokenLoginAPIView(ObtainAuthToken):
    throttle_classes = [LoginRateThrottle]


class EstadoAPIView(APIView):
    """
    Endpoint de ejemplo para confirmar que la API REST esta funcionando.

    Prueben visitarlo desde el navegador en:
        http://localhost:8000/api/estado/

    Sirve como punto de partida: reemplacen/amplien esta carpeta "api" con
    los serializers y vistas de los modelos reales de su organizacion
    (por ejemplo, ClienteSerializer, ClienteViewSet, etc.).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "estado": "ok",
                "mensaje": "La API REST del proyecto esta funcionando correctamente.",
            },
            status=status.HTTP_200_OK,
        )


class AuthMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                'id': request.user.pk,
                'username': request.user.get_username(),
                'groups': list(
                    request.user.groups.values_list('name', flat=True)
                ),
                'permissions': sorted(request.user.get_all_permissions()),
            }
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
