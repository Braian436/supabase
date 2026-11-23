from rest_framework.routers import DefaultRouter

from servicios.api.view import ServiciosViewSet

router = DefaultRouter()
router.register('servicios', ServiciosViewSet, basename='servicios')

urlpatterns = router.urls
