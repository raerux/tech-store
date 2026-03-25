from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework import status, viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Category, Product, Review, CartItem, Order
from .serializers import (
    RegisterSerializer, LoginSerializer, get_tokens_for_user,
    CategorySerializer, ProductSerializer, ReviewSerializer,
    CartItemSerializer, OrderSerializer, CreateOrderSerializer
)
from .permissions import IsAdminRole

User = get_user_model()

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response({
        "success": True,
        "message": "Usuário cadastrado com sucesso",
        "data": RegisterSerializer(user).data
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    user = authenticate(request, username=email, password=password)
    if not user:
        return Response(
            {"success": False, "message": "Credenciais inválidas"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    tokens = get_tokens_for_user(user)
    return Response({
        "success": True,
        "data": {
            "user": {"id": user.id, "nome": user.nome, "email": user.email, "role": user.role},
            "tokens": tokens
        }
    })

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by("nome")
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminRole()]
        return [AllowAny()]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("categoria").all().order_by("-created_at")
    serializer_class = ProductSerializer
    filterset_fields = ["categoria", "destaque"]
    search_fields = ["nome", "descricao"]
    ordering_fields = ["preco", "created_at", "nome"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminRole()]
        return [AllowAny()]

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("user", "product").all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.select_related("product").filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user.role == "ADMIN":
            return Order.objects.prefetch_related("items__product").all().order_by("-created_at")
        return Order.objects.prefetch_related("items__product").filter(user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            {"success": True, "message": "Pedido criado com sucesso", "data": OrderSerializer(order).data},
            status=status.HTTP_201_CREATED
        )

class OrderRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user.role == "ADMIN":
            return Order.objects.prefetch_related("items__product").all()
        return Order.objects.prefetch_related("items__product").filter(user=self.request.user)