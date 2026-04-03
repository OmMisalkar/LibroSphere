# app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from datetime import date
import logging
from .models import Book, BorrowRequest, Favorite, Genre
from .models import Order, Review, OrderItem
from django.db.models import Avg, Count
from .models import OrderItem, BorrowRequest


from .models import Book, BorrowRequest, Favorite
from .forms import BookForm


logger = logging.getLogger(__name__)

# ---------------- HOME / BOOK LIST ----------------

from django.db.models import Avg, Count, Q

def Home(request):
    q = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")   # 👈 GET sort value

    books = Book.objects.all()

    # 🔍 Search
    if q:
        books = books.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q)
        )

    # ⭐ Ratings
    books = books.annotate(
        avg_rating=Avg("review__rating"),
        review_count=Count("review")
    )

    # 🔽 Sorting / Filtering logic
    if sort == "price_low":
        books = books.order_by("price")

    elif sort == "price_high":
        books = books.order_by("-price")

    elif sort == "borrow":
        books = books.filter(is_second_hand=True)

    elif sort == "best":
        books = books.order_by("-review_count")

    return render(request, "app/home.html", {
        "books": books
    })


# ---------------- AUTH ----------------

from django.contrib.auth.models import User
from django.contrib import messages

def Registration(request):
    if request.method == "POST":
        username = request.POST.get("username")
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        cpassword = request.POST.get("confirm_password")

        if password != cpassword:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("register")

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    # ✅ THIS LINE FIXES THE ERROR
    return render(request, "app/registration.html")


def Login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )
        if user:
            login(request, user)
            return redirect("home")
        messages.error(request, "Invalid credentials")

    return render(request, "app/login.html")

def show_book(request):
    books = Book.objects.all()
    return render(request, "app/home.html", {"books": books})

@login_required
def signout(request):
    logout(request)
    return redirect("login")

# ---------------- ADD BOOK (SECOND HAND ONLY) ----------------

@login_required
def add(request):
    genres = Genre.objects.all()   # ✅ GET ALL GENRES

    if request.method == "POST":
        book = Book.objects.create(
            title=request.POST.get("title"),
            author=request.POST.get("author"),
            description=request.POST.get("description"),
            price=request.POST.get("price"),
            quantity=request.POST.get("quantity", 1),
            image=request.FILES.get("image"),
            is_second_hand=True
        )

        # ✅ SAVE SELECTED GENRES
        selected_genres = request.POST.getlist("genres")
        book.genres.set(selected_genres)

        messages.success(request, "Second-hand book added successfully")
        return redirect("home")

    return render(request, "app/add.html", {
        "genres": genres   # ✅ PASS TO TEMPLATE
    })

# ---------------- CART ----------------

@login_required
def cart_view(request):
    cart = request.session.get("cart", {})
    books = Book.objects.filter(id__in=cart.keys())

    items, total = [], 0
    for book in books:
        qty = cart.get(str(book.id), 0)
        subtotal = book.price * qty
        total += subtotal
        items.append({"book": book, "quantity": qty, "subtotal": subtotal})

    return render(request, "app/cart.html", {"items": items, "total": total})


@require_POST
@login_required
def add_to_cart(request, pk):
    cart = request.session.get("cart", {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session["cart"] = cart
    messages.success(request, "Added to cart")
    return redirect(request.META.get("HTTP_REFERER", "home"))

# ---------------- FAVORITES (DATABASE ONLY) ----------------

@login_required
def toggle_favorite(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    fav = Favorite.objects.filter(user=request.user, book=book)

    if fav.exists():
        fav.delete()
        messages.info(request, "Removed from favorites")
    else:
        Favorite.objects.create(user=request.user, book=book)
        messages.success(request, "Added to favorites")

    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related("book")
    return render(request, "app/favorites.html", {"favorites": favorites})


@login_required
def remove_favorite(request, book_id):
    Favorite.objects.filter(user=request.user, book_id=book_id).delete()
    return redirect("favorites")

# ---------------- BORROW ----------------

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Book, BorrowRequest

@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        days_required = int(request.POST.get("days_required"))

        BorrowRequest.objects.create(
            user=request.user,
            book=book,
            quantity=quantity,
            days_required=days_required
        )

        messages.success(request, "Borrow request sent")
        return redirect("home")

    return render(request, "app/borrow.html", {"book": book})



#@staff_member_required
def borrow_requests_admin(request):
    requests = BorrowRequest.objects.all().order_by("-created_at")
    return render(request, "app/borrow_requests.html", {"requests": requests})


from django.utils.timezone import now

@login_required
def my_borrow_requests(request):
    borrows = BorrowRequest.objects.filter(user=request.user)
    today = date.today()

    for b in borrows:
        if b.is_paid and b.return_date:
            b.days_left = (b.return_date - today).days
            b.overdue_days = abs(b.days_left) if b.days_left < 0 else 0
        else:
            b.days_left = None
            b.overdue_days = 0

    return render(
        request,
        "app/my_borrows.html",
        {"borrow_requests": borrows}
    )


@login_required
def borrow_checkout(request, pk):
    borrow = get_object_or_404(BorrowRequest, pk=pk, user=request.user)

    if request.method == "POST":
        borrow.address = request.POST.get("address")
        borrow.payment_method = request.POST.get("payment_method")
        borrow.is_paid = True
        borrow.save()
        messages.success(request, "Borrow placed successfully")
        return redirect("my_borrows")

    return render(request, "app/borrow_checkout.html", {"borrow": borrow})


@login_required
def extend_borrow(request, pk):
    borrow = get_object_or_404(BorrowRequest, pk=pk, user=request.user)

    if request.method == "POST":
        extra_days = int(request.POST.get("extra_days"))

        # 🔒 Do NOT update return date or fine here
        borrow.extension_days = extra_days
        borrow.extension_status = "pending"
        borrow.save()

        messages.info(
            request,
            "Extension request sent to admin. Waiting for approval."
        )

    return redirect("my_borrows")

    
@login_required
def create_book(request):
    return redirect("add")

@login_required
def delete_data(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, "Book deleted successfully")
    return redirect("home")


@login_required
def updated(request, pk):
    return redirect("home")


@login_required
def remove_from_cart(request, pk):
    cart = request.session.get("cart", {})
    cart.pop(str(pk), None)
    request.session["cart"] = cart
    return redirect("cart")


@login_required
def increase_cart_item(request, pk):
    cart = request.session.get("cart", {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session["cart"] = cart
    return redirect("cart")


@login_required
def decrease_cart_item(request, pk):
    cart = request.session.get("cart", {})
    if str(pk) in cart:
        cart[str(pk)] -= 1
        if cart[str(pk)] <= 0:
            cart.pop(str(pk))
    request.session["cart"] = cart
    return redirect("cart")


@login_required
def place_order(request):
    request.session["cart"] = {}
    messages.success(request, "Order placed successfully")
    return redirect("home")


@login_required
def profile_view(request):
    # ✅ Purchased books (from OrderItem)
    purchased_items = OrderItem.objects.filter(
        order__user=request.user
    ).select_related("book")

    # ✅ Borrowed books
    borrowed_items = BorrowRequest.objects.filter(
        user=request.user,
        status="approved"
    ).select_related("book")

    context = {
        "purchased_items": purchased_items,
        "borrowed_items": borrowed_items,
        "purchased_count": purchased_items.count(),
        "borrowed_count": borrowed_items.count(),
    }

    return render(request, "app/profile.html", context)

@login_required
def checkout(request):
    cart = request.session.get("cart", {})
    books = Book.objects.filter(id__in=cart.keys())

    items = []
    total = 0
    for book in books:
        qty = cart[str(book.id)]
        subtotal = book.price * qty
        total += subtotal
        items.append({
            "book": book,
            "quantity": qty,
            "subtotal": subtotal
        })

    if request.method == "POST":
        # 👉 CREATE ORDER HERE
        order = Order.objects.create(
            user=request.user,
            total_amount=total
        )

        for it in items:
            OrderItem.objects.create(
                order=order,
                book=it["book"],
                quantity=it["quantity"],
                price=it["book"].price
            )

        request.session["cart"] = {}
        return redirect("order_success")

    return render(request, "app/checkout.html", {
        "items": items,
        "total": total
    })




@login_required
def checkout_view(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    books = Book.objects.filter(id__in=cart.keys())

    items = []
    total = 0

    for book in books:
        qty = int(cart[str(book.id)])
        subtotal = book.price * qty
        total += subtotal
        items.append({
            "book": book,
            "quantity": qty,
            "subtotal": subtotal
        })

    # ✅ CREATE ORDER ON POST
    if request.method == "POST":
        order = Order.objects.create(
            user=request.user,
            total_amount=total
        )

        for it in items:
            OrderItem.objects.create(
                order=order,
                book=it["book"],
                quantity=it["quantity"],
                price=it["book"].price
            )

        request.session["cart"] = {}
        messages.success(request, "Order placed successfully!")
        return redirect("order_success")

    return render(request, "app/checkout.html", {
        "items": items,
        "total": total
    })

@login_required
def order_success(request):
    return render(request, "app/order_success.html")

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, "app/book_detail.html", {"book": book})

@login_required
def add_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        Review.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={
                "rating": request.POST.get("rating"),
                "comment": request.POST.get("comment"),
            }
        )
        messages.success(request, "Thank you for your feedback!")
        return redirect("profile")

    return render(request, "app/review.html", {"book": book})

@login_required
def place_order(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    books = Book.objects.filter(id__in=cart.keys())

    # ✅ Create order first
    order = Order.objects.create(
        user=request.user,
        total_amount=0
    )

    total = 0

    for book in books:
        qty = int(cart.get(str(book.id), 0))
        subtotal = book.price * qty
        total += subtotal

        # ✅ Create order items
        OrderItem.objects.create(
            order=order,
            book=book,
            quantity=qty,
            price=book.price
        )

    # ✅ VERY IMPORTANT: update total
    order.total_amount = total
    order.save()

    # ✅ Clear cart AFTER saving
    request.session["cart"] = {}

    messages.success(request, "Order placed successfully!")
    return redirect("order_success")


def can_user_rate(user, book):
    # ✅ Purchased?
    purchased = OrderItem.objects.filter(
        order__user=user,
        book=book
    ).exists()

    # ✅ Borrowed & return date passed?
    borrowed_and_returned = BorrowRequest.objects.filter(
        user=user,
        book=book,
        return_date__lt=date.today(),
        status="approved"
    ).exists()

    return purchased or borrowed_and_returned

@login_required
def add_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not can_user_rate(request.user, book):
        messages.error(request, "You can rate only after purchase or return.")
        return redirect("book_detail", pk=book.id)

    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment", "")

        Review.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={
                "rating": rating,
                "comment": comment
            }
        )

        messages.success(request, "Thanks for your review!")
        return redirect("book_detail", pk=book.id)

    return redirect("book_detail", pk=book.id)

@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)

    can_rate = can_user_rate(request.user, book)

    review = Review.objects.filter(book=book)

    return render(request, "app/book_detail.html", {
        "book": book,
        "can_rate": can_rate,
        "review": review
    })
from django.db.models import Sum
from .models import OrderItem, BorrowRequest, Order
from django.db.models import Sum
from .models import OrderItem, BorrowRequest
from django.db.models import Sum
import json
from django.db.models import Sum
import json
from django.db.models import Sum
from django.db.models import Sum
import json
from django.db.models import Sum
from django.db.models.functions import TruncDate
import json
from django.db.models import Sum
from django.db.models.functions import TruncDate
import json
from django.db.models import Sum
from django.db.models.functions import TruncDate
import json

def comparison_dashboard(request):

    # 🛒 RECORDS
    sold_records = OrderItem.objects.select_related('order__user', 'book', 'order')
    borrowed_records = BorrowRequest.objects.select_related('user', 'book')

    # 📊 TOTALS
    total_sold = OrderItem.objects.aggregate(total=Sum('quantity'))['total'] or 0
    total_borrowed = BorrowRequest.objects.aggregate(total=Sum('quantity'))['total'] or 0

    # 📅 PURCHASE TREND
    purchase_data = OrderItem.objects.annotate(
        date=TruncDate('order__created_at')
    ).values('date').annotate(total=Sum('quantity')).order_by('date')

    purchase_labels = [str(i['date']) for i in purchase_data]
    purchase_values = [i['total'] for i in purchase_data]

    # 📅 BORROW TREND
    borrow_data = BorrowRequest.objects.values('borrow_date') \
        .annotate(total=Sum('quantity')).order_by('borrow_date')

    borrow_labels = [str(i['borrow_date']) for i in borrow_data]
    borrow_values = [i['total'] for i in borrow_data]

    # 📚 SALES PER BOOK
    book_sales = OrderItem.objects.values('book__title') \
        .annotate(total=Sum('quantity')).order_by('-total')

    book_labels = [b['book__title'] for b in book_sales]
    book_values = [b['total'] for b in book_sales]

    context = {
        'sold_records': sold_records,
        'borrowed_records': borrowed_records,

        'total_sold': total_sold,
        'total_borrowed': total_borrowed,

        'purchase_labels': json.dumps(purchase_labels),
        'purchase_values': json.dumps(purchase_values),

        'borrow_labels': json.dumps(borrow_labels),
        'borrow_values': json.dumps(borrow_values),

        'book_labels': json.dumps(book_labels),
        'book_values': json.dumps(book_values),
    }

    return render(request, "app/comparison.html", context)