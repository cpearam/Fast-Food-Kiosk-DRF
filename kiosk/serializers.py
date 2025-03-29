from rest_framework import serializers
from .models import StaffMember, Product, ComboMeal, Order, OrderItem
from django.db import transaction

class StaffMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffMember
        fields = ('id', 'name', 'position', 'branch', 'username', 'email')
        
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('name', 'price', 'stock')
        
class ComboMealSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_ids = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        many=True,
        write_only=True
    )
    price = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    discount = serializers.IntegerField(
        min_value=0, max_value=100
    )
    
    class Meta: 
        model = ComboMeal
        fields = ('id','name', 'products', 'product_ids','discount', 'price', 'is_available')
        read_only_fields = ['is_available', 'price']
        
    def get_price(self, obj):
        return obj.price
    
    def get_is_available(self, obj):
        return obj.is_available
        
    # def validate(self, value):
    #     product_ids = self.initial_data.get('product_ids', [])
    #     products = Product.objects.filter(id__in=product_ids)
        
    #     if any(product.stock <= 0 for product in products):
    #         raise serializers.ValidationError("No stock available")
    #     return value
    
    def create(self, validated_data):
        """Handle Many-to-Many relation during creation"""
        product_ids = validated_data.pop('product_ids', [])
        combo_meal = ComboMeal.objects.create(**validated_data)
        combo_meal.products.set(product_ids)  # Set ManyToMany relation
        return combo_meal

    def update(self, instance, validated_data):
        """Update combo meal with new products"""
        product_ids = validated_data.pop('product_ids', None)
        if product_ids is not None:
            instance.products.set(product_ids)
        return super().update(instance, validated_data)
    
class OrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False)
    combomeal_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField()

    def validate(self, data):
        # Make sure either product_id or combomeal_id is provided, but not both
        if not data.get('product_id') and not data.get('combomeal_id'):
            raise serializers.ValidationError("Either product_id or combomeal_id must be provided.")
        if data.get('product_id') and data.get('combomeal_id'):
            raise serializers.ValidationError("You cannot provide both product_id and combomeal_id at the same time.")
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Expect a list of items in the request
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = ('order_id', 'staff', 'items', 'created_at', 'total_price')

    def create(self, validated_data):
        """Reduce stock and create an order"""
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)

        with transaction.atomic():  # Ensure atomicity
            for item_data in items_data:
                product_id = item_data.get('product_id')
                combomeal_id = item_data.get('combomeal_id')
                quantity = item_data.get('quantity')

                if product_id:
                    # Handle individual product
                    product = Product.objects.get(id=product_id)
                    if product.stock < quantity:
                        raise serializers.ValidationError(
                            f"Insufficient stock for product {product.name}. Available: {product.stock}"
                        )
                    product.stock -= quantity
                    product.save()

                    # Create the order item for the product
                    OrderItem.objects.create(
                        order=order, product=product, quantity=quantity, total_price=product.price * quantity
                    )

                elif combomeal_id:
                    # Handle combo meal
                    combomeal = ComboMeal.objects.get(id=combomeal_id)
                    for product in combomeal.products.all():
                        if product.stock < quantity:
                            raise serializers.ValidationError(
                                f"Insufficient stock for product {product.name} in combo meal {combomeal.name}. "
                                f"Available: {product.stock}"
                            )
                        product.stock -= quantity
                        product.save()

                    # Create the order item for the combo meal
                    OrderItem.objects.create(
                        order=order, combomeal=combomeal, quantity=quantity, total_price=combomeal.price * quantity
                    )

        return order