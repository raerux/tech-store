from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Product, Review, CartItem, Order, OrderItem, create_order_from_cart

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "nome", "email", "password"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            nome=validated_data["nome"],
            role="CUSTOMER"
        )

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "nome", "slug"]

class ProductSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source="categoria.nome", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "nome", "descricao", "preco", "imagem_url", "estoque",
            "destaque", "categoria", "categoria_nome", "created_at"
        ]

class ReviewSerializer(serializers.ModelSerializer):
    user_nome = serializers.CharField(source="user.nome", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "rating", "comentario", "user", "user_nome", "product"]
        read_only_fields = ["user"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("rating deve ser entre 1 e 5")
        return value

class CartItemSerializer(serializers.ModelSerializer):
    product_nome = serializers.CharField(source="product.nome", read_only=True)
    preco = serializers.DecimalField(source="product.preco", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "user", "product", "product_nome", "preco", "quantidade"]
        read_only_fields = ["user"]

    def validate_quantidade(self, value):
        if value <= 0:
            raise serializers.ValidationError("quantidade deve ser maior que 0")
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    product_nome = serializers.CharField(source="product.nome", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_nome", "quantidade", "preco_unitario"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "total", "created_at", "items"]
        read_only_fields = ["user", "total", "created_at"]

class CreateOrderSerializer(serializers.Serializer):
    def create(self, validated_data):
        user = self.context["request"].user
        order = create_order_from_cart(user)
        return order

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }