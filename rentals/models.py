from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("jewellery", "Jewellery"),
        ("clothing", "Clothing & sarees"),
        ("accessories", "Accessories"),
        ("electronics", "Electronics"),
        ("home", "Home & tools"),
        ("other", "Other"),
    ]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listed_products")
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    photo = models.ImageField(upload_to="products/", blank=True, null=True)
    replacement_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Reference value of the item")
    daily_rent = models.DecimalField(max_digits=8, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    condition_notes = models.CharField(max_length=250, blank=True, help_text="Describe existing marks or missing parts")
    location_name = models.CharField(max_length=160, help_text="Neighbourhood or public pickup area; do not enter a public-facing home address")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Booking(models.Model):
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("active", "Rental active"),
        ("return_review", "Return under review"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("disputed", "Disputed"),
    ]
    DELIVERY_CHOICES = [("pickup", "Direct pickup"), ("owner_delivery", "Owner-arranged delivery")]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="bookings")
    renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rental_bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default="pickup")
    delivery_total = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    renter_delivery_share = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    owner_delivery_share = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    agreed_rent = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
    agreed_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    renter_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    promo_code_used = models.CharField(max_length=32, blank=True)
    discount_amount = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
    proposed_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    deduction_reason = models.TextField(blank=True)
    owner_return_confirmed = models.BooleanField(default=False)
    renter_return_confirmed = models.BooleanField(default=False)
    handover_notes = models.TextField(blank=True)
    return_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def rental_days(self):
        return max((self.end_date - self.start_date).days, 1)

    @property
    def rental_total(self):
        return self.agreed_rent

    @property
    def estimated_renter_total(self):
        return self.agreed_rent + self.agreed_deposit + self.renter_delivery_share

    @property
    def estimated_refund(self):
        return max(self.agreed_deposit - self.proposed_deduction, Decimal("0.00"))

    def __str__(self):
        return f"Booking #{self.pk} - {self.product.title}"


class ConditionReport(models.Model):
    STAGE_CHOICES = [("handover", "Before handover"), ("return", "On return")]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="condition_reports")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stage = models.CharField(max_length=12, choices=STAGE_CHOICES)
    photo = models.ImageField(upload_to="condition_reports/", blank=True, null=True)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.booking_id} - {self.stage} report"


class Message(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_rental_messages")
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message {self.pk} for booking {self.booking_id}"


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} star") for i in range(1, 6)])
    comment = models.TextField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=180)
    message = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject


class Complaint(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="complaints", null=True, blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=80)
    details = models.TextField(max_length=3000)
    status = models.CharField(max_length=20, choices=[("open", "Open"), ("reviewing", "Reviewing"), ("resolved", "Resolved")], default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Complaint #{self.pk}: {self.category}"

# NearRent feature pack: 13 implemented marketplace features.
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nearrent_profile')
    verification_status = models.CharField(max_length=20, choices=[('unverified','Not submitted'),('pending','Pending review'),('verified','Verified')], default='unverified')
    verification_note = models.CharField(max_length=250, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f'{self.user.username} profile'

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','product'], name='unique_user_wishlist_product')]
        ordering = ['-created_at']

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='product_reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, f'{i} star') for i in range(1,6)])
    comment = models.TextField(max_length=1200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['booking','reviewer'], name='unique_booking_reviewer_review')]
        ordering = ['-created_at']

class ProductAvailability(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='blocked_dates')
    date = models.DateField()
    note = models.CharField(max_length=160, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['product','date'], name='unique_product_blocked_date')]
        ordering = ['date']

class ExtensionRequest(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='extension_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    proposed_end_date = models.DateField()
    reason = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=12, choices=[('pending','Pending'),('approved','Approved'),('declined','Declined')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class CancellationRequest(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='cancellation_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=500)
    status = models.CharField(max_length=12, choices=[('pending','Pending'),('approved','Approved'),('declined','Declined')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class PromoCode(models.Model):
    code = models.CharField(max_length=32, unique=True)
    percent_off = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=100)
    uses = models.PositiveIntegerField(default=0)
    def __str__(self): return self.code
    @property
    def is_valid_now(self): return self.active and self.uses < self.max_uses and (self.valid_until is None or self.valid_until >= timezone.localdate()) and 0 <= self.percent_off <= 100

class SavedSearch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_rental_searches')
    query = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class BookingReminder(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=240)
    remind_on = models.DateField()
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ListingReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=80, choices=[('spam','Spam or duplicate'),('misleading','Misleading details'),('prohibited','Unsafe or prohibited item'),('scam','Suspected scam'),('other','Other')])
    details = models.TextField(max_length=1200, blank=True)
    status = models.CharField(max_length=12, choices=[('open','Open'),('reviewing','Reviewing'),('resolved','Resolved')], default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
