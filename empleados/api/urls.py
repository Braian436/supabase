from rest_framework.routers import DefaultRouter
from empleados.api.view import EmpleadosViewSet

router= DefaultRouter()
router.register('empleados', EmpleadosViewSet, basename='empleados' )
urlpatterns = router.urls
