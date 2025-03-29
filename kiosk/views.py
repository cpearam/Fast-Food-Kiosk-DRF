from django.shortcuts import render
from rest_framework import viewsets
from .models import StaffMember, Product, ComboMeal, Order
from .serializers import StaffMemberSerializer, ProductSerializer, ComboMealSerializer, OrderSerializer

class StaffMemberViewSet(viewsets.ModelViewSet):
    queryset = StaffMember.objects.all()
    serializer_class = StaffMemberSerializer
    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
class ComboMealViewSet(viewsets.ModelViewSet):
    queryset = ComboMeal.objects.prefetch_related('products')
    serializer_class = ComboMealSerializer
    
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product', 'items__combomeal')
    serializer_class = OrderSerializer
