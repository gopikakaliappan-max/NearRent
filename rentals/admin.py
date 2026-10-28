from django.contrib import admin
from .models import Product, Booking, ConditionReport, Message, Feedback, ContactMessage, Complaint, Wishlist, UserProfile, ProductReview, ProductAvailability, ExtensionRequest, CancellationRequest, PromoCode, SavedSearch, BookingReminder, ListingReport

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "daily_rent", "is_available", "created_at")
    list_filter = ("category", "is_available")
    search_fields = ("title", "description", "location_name", "owner__username")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "renter", "start_date", "end_date", "status", "created_at")
    list_filter = ("status", "delivery_method")
    search_fields = ("product__title", "renter__username")

admin.site.register(ConditionReport)
admin.site.register(Message)
admin.site.register(Feedback)
admin.site.register(ContactMessage)
admin.site.register(Complaint)

admin.site.register([Wishlist, UserProfile, ProductReview, ProductAvailability, ExtensionRequest, CancellationRequest, PromoCode, SavedSearch, BookingReminder, ListingReport])
