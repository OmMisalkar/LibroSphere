from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="books/", blank=True, null=True)
    is_second_hand = models.BooleanField(default=False)

    genres = models.ManyToManyField(Genre, blank=True)

    def __str__(self):
        return self.title

    # --- Cart & Favorite models (append below existing model definitions) ---
from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Cart({self.user.username})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('cart','book')

    def __str__(self):
        return f"{self.book.title} x{self.quantity}"

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user','book')

    def __str__(self):
        return f"Fav({self.user.username}:{self.book.title})"


from django.contrib.auth.models import User

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class BorrowRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    EXTENSION_STATUS_CHOICES = [
        ('none', 'None'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    days_required = models.PositiveIntegerField()

    borrow_date = models.DateField(default=timezone.now)
    return_date = models.DateField(blank=True, null=True)

    extended_days = models.PositiveIntegerField(default=0)
    extra_fine = models.PositiveIntegerField(default=0)

    extension_days = models.PositiveIntegerField(default=0)
    extension_status = models.CharField(
        max_length=10,
        choices=EXTENSION_STATUS_CHOICES,
        default='none'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.return_date:
            self.return_date = self.borrow_date + timedelta(days=self.days_required)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.book}"



from django.conf import settings

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.book.title} x {self.quantity}"






class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")  # 1 review per user per book

    def __str__(self):
        return f"{self.user} - {self.book} ({self.rating})"

