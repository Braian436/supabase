from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.dashboard import obtener_resumen_dashboard


class DashboardFechasSerializer(serializers.Serializer):
    fecha_caja = serializers.DateField(required=False)
    fecha_barberos = serializers.DateField(required=False)
    fecha_cortes = serializers.DateField(required=False)


class DashboardAdministradorAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = DashboardFechasSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        hoy = timezone.localdate()
        fechas = serializer.validated_data
        resumen = obtener_resumen_dashboard(
            fecha_hoy=hoy,
            fecha_caja=fechas.get('fecha_caja', hoy),
            fecha_barberos=fechas.get('fecha_barberos', hoy),
            fecha_cortes=fechas.get('fecha_cortes', hoy),
        )
        return Response(resumen, status=status.HTTP_200_OK)


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
