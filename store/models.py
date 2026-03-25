from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.text import slugify
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, nome="", role="CUSTOMER", **extra_fields):
        if not email:
            raise ValueError("Email é obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, role=role, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, password=password, role="ADMIN", **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ("ADMIN", "ADMIN"),
        ("CUSTOMER", "CUSTOMER"),
    )
    username = models.CharField(max_length=150, unique=True)
    nome = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="CUSTOMER")
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class Category(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Product(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem_url = models.URLField(blank=True, null=True)
    estoque = models.PositiveIntegerField(default=0)
    destaque = models.BooleanField(default=False)
    categoria = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Review(models.Model):
    rating = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")

    class Meta:
        unique_together = ("user", "product")

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Rating deve ser entre 1 e 5")

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("user", "product")

class Order(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "PENDING"),
        ("PAID", "PAID"),
        ("CANCELED", "CANCELED"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

def create_order_from_cart(user):
    cart_items = CartItem.objects.select_related("product").filter(user=user)
    if not cart_items.exists():
        raise ValidationError("Carrinho vazio")

    with transaction.atomic():
        order = Order.objects.create(user=user, status="PENDING", total=Decimal("0.00"))
        total = Decimal("0.00")

        for item in cart_items:
            product = Product.objects.select_for_update().get(pk=item.product_id)

            if product.estoque < item.quantidade:
                raise ValidationError(f"Sem estoque para: {product.nome}")

            product.estoque -= item.quantidade
            product.save()

            subtotal = product.preco * item.quantidade
            total += subtotal

            OrderItem.objects.create(
                order=order,
                product=product,
                quantidade=item.quantidade,
                preco_unitario=product.preco
            )

        order.total = total
        order.save()
        cart_items.delete()

    return order