from rest_framework.routers import DefaultRouter

from servicios.api.view import EmpleadosServiciosViewSet, ServiciosViewSet

router = DefaultRouter()
router.register('servicios', ServiciosViewSet, basename='servicios')
router.register('empleados-servicios', EmpleadosServiciosViewSet, basename='empleados-servicios')

urlpatterns = router.urls
