from rest_framework.routers import DefaultRouter

from .views import VentasViewSet

router = DefaultRouter()
router.register('ventas', VentasViewSet, basename='ventas')

urlpatterns = router.urls
