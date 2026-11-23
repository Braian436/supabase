from django.urls import path

from compras.api.view import ComprasAPIView

urlpatterns = [
    path('compras/', ComprasAPIView.as_view(), name='compras-list'),
]
