from rest_framework import generics, status
from rest_framework.response import Response

from compras.api.serializer import CompraCreateSerializer, CompraSerializer
from compras.models import Compras


class ComprasAPIView(generics.ListCreateAPIView):
    queryset = Compras.objects.prefetch_related(
        'detallescompras_set__id_producto',
    ).order_by('-fecha', '-id_compra')

    def get_serializer_class(self):
        return CompraCreateSerializer if self.request.method == 'POST' else CompraSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        compra = serializer.save()
        return Response(CompraSerializer(compra).data, status=status.HTTP_201_CREATED)
