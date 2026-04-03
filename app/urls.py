from django.urls import path
from . import views

urlpatterns = [
    path("", views.Login_view, name="login"),
    path("home/", views.Home, name="home"),
    #path("register/", views.Register, name="register"),
    path("register/", views.Registration, name="register"),
    path("registration/", views.Registration, name="registration"),
    path("logout/", views.signout, name="logout"),

    # Books
    path("add/", views.add, name="add"),
    path("show-book/", views.show_book, name="show_book"),
    path("delete/<int:pk>/", views.delete_data, name="delete"),
    path("update/<int:pk>/", views.updated, name="updated_data"),

    # Cart
    path("add-to-cart/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("remove-from-cart/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/increase/<int:pk>/", views.increase_cart_item, name="increase_cart"),
    path("cart/decrease/<int:pk>/", views.decrease_cart_item, name="decrease_cart"),
    path("place-order/", views.place_order, name="place_order"),

    # Favorites
    path("favorites/", views.favorites_view, name="favorites"),
    path("favorite/<int:book_id>/", views.toggle_favorite, name="toggle_favorite"),
    path("remove-favorite/<int:book_id>/", views.remove_favorite, name="remove_favorite"),

    # Borrow
    path("borrow/<int:book_id>/", views.borrow_book, name="borrow_book"),
    path('borrow-checkout/<int:pk>/', views.borrow_checkout, name='borrow_checkout'),
    path("my-borrows/", views.my_borrow_requests, name="my_borrows"),
    path("extend-borrow/<int:pk>/", views.extend_borrow, name="extend_borrow"),

    # Profile
    path("profile/", views.profile_view, name="profile"),

    #checkout
    path("checkout/", views.checkout_view, name="checkout"),
    path("order-success/", views.order_success, name="order_success"),

    #book details
    path("book/<int:pk>/", views.book_detail, name="book_detail"),

    #review
    path("review/<int:book_id>/", views.add_review, name="add_review"),

    path('comparison/', views.comparison_dashboard, name='comparison'),
    path('comparison/', views.comparison_dashboard, name='comparison'),
]
