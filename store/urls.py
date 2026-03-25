from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    register, login,
    CategoryListCreateView,
    ProductViewSet, ReviewViewSet,
    CartItemViewSet,
    OrderListCreateView, OrderRetrieveView
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")
router.register(r"reviews", ReviewViewSet, basename="reviews")
router.register(r"cart", CartItemViewSet, basename="cart")

urlpatterns = [
    path("auth/register", register),
    path("auth/login", login),

    path("categories", CategoryListCreateView.as_view()),
    path("orders", OrderListCreateView.as_view()),
    path("orders/<int:pk>", OrderRetrieveView.as_view()),

    path("", include(router.urls)),
]