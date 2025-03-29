from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    
]

router = DefaultRouter()
router.register('staff', views.StaffMemberViewSet)
router.register('product', views.ProductViewSet)
router.register('combomeal', views.ComboMealViewSet)
router.register('order', views.OrderViewSet)
urlpatterns += router.urls
