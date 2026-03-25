from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Product, Review, CartItem, Order, OrderItem

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("id", "email", "nome", "role", "is_staff", "created_at")
    ordering = ("-created_at",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Dados extras", {"fields": ("nome", "role", "created_at")}),
    )
    readonly_fields = ("created_at",)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Review)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)