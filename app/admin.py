from django.contrib import admin
from django.utils.html import format_html
from datetime import timedelta
from .models import Book, BorrowRequest, Genre


# ✅ Register Genre (simple)
admin.site.register(Genre)


# ✅ Book admin (registered ONLY here)
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'is_second_hand', 'image_tag')
    search_fields = ('title', 'author')
    list_filter = ('is_second_hand',)
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:100px; max-width:100px;" />',
                obj.image.url
            )
        return 'No Image'

    image_tag.short_description = 'Image'


# ✅ BorrowRequest admin
@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'book', 'quantity',
        'days_required', 'status',
        'extension_status', 'extension_days',
        'return_date', 'extra_fine'
    )

    list_filter = ('status', 'extension_status')
    search_fields = ('user__username', 'book__title')

    actions = [
        'approve_requests',
        'reject_requests',
        'approve_extension',
        'reject_extension'
    ]

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, "Selected borrow requests approved.")

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, "Selected borrow requests rejected.")

    def approve_extension(self, request, queryset):
        for borrow in queryset:
            if borrow.extension_status == 'pending':
                borrow.extended_days += borrow.extension_days
                borrow.extra_fine += borrow.extension_days * 10
                borrow.return_date += timedelta(days=borrow.extension_days)

                borrow.extension_status = 'approved'
                borrow.extension_days = 0
                borrow.save()

        self.message_user(request, "Selected extension requests approved.")

    def reject_extension(self, request, queryset):
        queryset.update(
            extension_status='rejected',
            extension_days=0
        )
        self.message_user(request, "Selected extension requests rejected.")

    approve_requests.short_description = "Approve borrow request"
    reject_requests.short_description = "Reject borrow request"
    approve_extension.short_description = "Approve extension request"
    reject_extension.short_description = "Reject extension request"


from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_amount", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "book", "quantity", "price")
    search_fields = ("book__title",)
