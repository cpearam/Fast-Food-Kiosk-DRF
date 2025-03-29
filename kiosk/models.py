from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from decimal import Decimal

class StaffMember(AbstractUser):
    POSITION_CHOICES = [
        ('manager','Manager'),
        ('staff','Staff'),
        ('cashier','Cashier')
    ]
    name = models.CharField(max_length=45)
    branch = models.CharField(max_length=45)
    position = models.CharField(max_length=45, choices=POSITION_CHOICES, default='staff')
    
    def __str__(self):
        return f"{self.name} - {self.get_position_display()}"

class Product(models.Model):
    name = models.CharField(max_length=25)
    price = models.DecimalField(max_digits=4, decimal_places=2)
    stock = models.PositiveIntegerField()
    
    def __str__(self):
        return self.name
    
class ComboMeal(models.Model):
    name = models.CharField(max_length=25, unique=True)
    products = models.ManyToManyField(Product, related_name='combomeals')
    discount = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=4, decimal_places=2)
    is_available = models.BooleanField(default=False)
    
    @property
    def price(self):
        total_price = sum(product.price for product in self.products.all())
        discounted_price = Decimal(total_price) * (Decimal(1) - Decimal(self.discount) / Decimal(100))
        return discounted_price
    
    @property
    def is_available(self):
        is_available = all(product.stock > 0 for product in self.products.all())
        return is_available
    
    def __str__(self):
        return f'{self.name} is {self.is_available}'
    
class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    products = models.ManyToManyField(Product, through='OrderItem', related_name='products')
    combomeals = models.ManyToManyField(ComboMeal, through='OrderItem', related_name='combomeals')
    
    @property
    def total_price(self):
        """Calculate the total price of the order based on its items"""
        total = 0
        for item in self.items.all():  # Using related_name 'items' to access OrderItems
            if item.product:
                total += item.product.price * item.quantity
            elif item.combomeal:
                total += item.combomeal.price * item.quantity
        return total
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE)
    combomeal = models.ForeignKey(ComboMeal, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=4, decimal_places=2)
    
    def __str__(self):
        if self.product:
            return f"{self.quantity} x {self.product.name} in Order {self.order.order_id}"
        elif self.combomeal:
            return f"{self.quantity} x {self.combomeal.name} in Order {self.order.order_id}"