import json
import math
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import RegisterForm, ProductForm, BookingForm, FeedbackForm, ContactForm, ConditionReportForm, ComplaintForm
from .models import Product, Booking, Message, Feedback, ContactMessage, ConditionReport, Complaint


def home(request):
    products = Product.objects.filter(is_available=True).select_related("owner")[:8]
    return render(request, "rentals/home.html", {"products": products})


def about(request):
    return render(request, "rentals/about.html")


def terms(request):
    return render(request, "rentals/terms.html")


def product_list(request):
    products = Product.objects.filter(is_available=True).select_related("owner")
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    lat_raw, lon_raw = request.GET.get("lat", "").strip(), request.GET.get("lon", "").strip()
    radius_applied = False
    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location_name__icontains=query))
    if category:
        products = products.filter(category=category)
    if lat_raw and lon_raw:
        try:
            user_lat, user_lon = float(lat_raw), float(lon_raw)
            if not (-90 <= user_lat <= 90 and -180 <= user_lon <= 180):
                raise ValueError
            def km_distance(product):
                if product.latitude is None or product.longitude is None:
                    return None
                p_lat, p_lon = float(product.latitude), float(product.longitude)
                lat1, lat2 = math.radians(user_lat), math.radians(p_lat)
                dlat, dlon = math.radians(p_lat - user_lat), math.radians(p_lon - user_lon)
                a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0, 1 - a)))
            products = [p for p in products if km_distance(p) is not None and km_distance(p) <= 10]
            radius_applied = True
        except ValueError:
            messages.error(request, "Enter valid latitude and longitude to filter within 10 km.")
    return render(request, "rentals/product_list.html", {
        "products": products, "query": query, "category": category,
        "categories": Product.CATEGORY_CHOICES, "lat": lat_raw, "lon": lon_raw,
        "radius_applied": radius_applied,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("owner"), pk=pk, is_available=True)
    return render(request, "rentals/product_detail.html", {"product": product})


@login_required
def register_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            messages.success(request, "Your listing is live.")
            return redirect("product_detail", pk=product.pk)
    else:
        form = ProductForm()
    return render(request, "rentals/product_form.html", {"form": form})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.save()
            login(request, user)
            messages.success(request, "Welcome to NearRent! Your account is ready.")
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def create_booking(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    if product.owner_id == request.user.id:
        messages.error(request, "You cannot rent your own listing.")
        return redirect("product_detail", pk=product.pk)
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            start, end = form.cleaned_data["start_date"], form.cleaned_data["end_date"]
            if start < date.today():
                form.add_error("start_date", "Start date cannot be in the past.")
            overlapping = Booking.objects.filter(
                product=product,
                status__in=["requested", "accepted", "active", "return_review"],
                start_date__lte=end, end_date__gte=start
            ).exists()
            if overlapping:
                form.add_error(None, "This item already has a booking request for overlapping dates.")
            if not form.errors:
                booking = form.save(commit=False)
                booking.product = product
                booking.renter = request.user
                booking.agreed_rent = product.daily_rent * Decimal(max((end - start).days + 1, 1))
                booking.agreed_deposit = product.security_deposit
                booking.delivery_total = form.cleaned_data["delivery_total"] or Decimal("0.00")
                booking.renter_delivery_share = (booking.delivery_total / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                booking.owner_delivery_share = booking.delivery_total - booking.renter_delivery_share
                booking.renter_paid_amount = booking.agreed_rent + booking.agreed_deposit + booking.renter_delivery_share
                booking.save()
                messages.success(request, "Rental request sent. The owner can now review it and message you.")
                return redirect("orders")
    else:
        form = BookingForm(initial={"delivery_method": "pickup", "delivery_total": "0.00"})
    return render(request, "rentals/booking_form.html", {"form": form, "product": product})


@login_required
def orders(request):
    bookings = Booking.objects.filter(Q(renter=request.user) | Q(product__owner=request.user)).select_related("product", "renter", "product__owner").distinct()
    return render(request, "rentals/orders.html", {"bookings": bookings})


def _booking_participant(booking, user):
    return booking.renter_id == user.id or booking.product.owner_id == user.id


@login_required
def booking_action(request, pk, action):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    booking = get_object_or_404(Booking.objects.select_related("product", "renter", "product__owner"), pk=pk)
    if not _booking_participant(booking, request.user):
        raise PermissionDenied
    is_owner = booking.product.owner_id == request.user.id
    if action == "accept" and is_owner and booking.status == "requested":
        booking.status = "accepted"
        messages.success(request, "Booking accepted. Coordinate handover in messages.")
    elif action == "decline" and is_owner and booking.status == "requested":
        booking.status = "declined"
        messages.info(request, "Booking declined.")
    elif action == "handover" and is_owner and booking.status == "accepted":
        booking.status = "active"
        messages.success(request, "Handover recorded. Remember to save condition photos.")
    elif action == "return" and booking.status == "active":
        booking.status = "return_review"
        messages.success(request, "Return submitted for review. Both parties should confirm the condition.")
    elif action == "confirm-return" and booking.status == "return_review":
        if is_owner:
            booking.owner_return_confirmed = True
        else:
            booking.renter_return_confirmed = True
        if booking.owner_return_confirmed and booking.renter_return_confirmed:
            booking.status = "completed"
            messages.success(request, "Both parties confirmed the return. Rental marked completed.")
        else:
            messages.success(request, "Your confirmation was recorded; waiting for the other party.")
    else:
        messages.error(request, "That action is not available for this booking.")
    booking.save()
    return redirect("orders")


@login_required
def condition_report(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("product"), pk=pk)
    if not _booking_participant(booking, request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = ConditionReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.booking = booking
            report.created_by = request.user
            report.save()
            messages.success(request, "Condition report saved.")
            return redirect("orders")
    else:
        form = ConditionReportForm()
    return render(request, "rentals/condition_report.html", {"form": form, "booking": booking})


@login_required
def chat_room(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("product", "renter", "product__owner"), pk=pk)
    if not _booking_participant(booking, request.user):
        raise PermissionDenied
    return render(request, "rentals/chat_room.html", {"booking": booking})


@login_required
def messages_api(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("product"), pk=pk)
    if not _booking_participant(booking, request.user):
        raise PermissionDenied
    if request.method == "GET":
        after = request.GET.get("after", "0")
        try:
            after_id = int(after)
        except ValueError:
            return HttpResponseBadRequest("Invalid message cursor")
        msgs = booking.messages.filter(id__gt=after_id).select_related("sender")
        data = [{
            "id": m.id,
            "sender": m.sender.get_full_name() or m.sender.username,
            "mine": m.sender_id == request.user.id,
            "body": m.body,
            "created_at": timezone.localtime(m.created_at).strftime("%d %b, %I:%M %p"),
        } for m in msgs]
        return JsonResponse({"messages": data})
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if not body or len(body) > 2000:
            return HttpResponseBadRequest("Message must be 1-2000 characters.")
        message = Message.objects.create(booking=booking, sender=request.user, body=body)
        return JsonResponse({"ok": True, "id": message.id})
    return HttpResponseBadRequest("GET or POST required")


@login_required
def feedback(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, "Thank you for your feedback.")
            return redirect("feedback")
    else:
        form = FeedbackForm()
    return render(request, "rentals/feedback.html", {"form": form, "recent_feedback": Feedback.objects.select_related("user")[:5]})


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent.")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "rentals/contact.html", {"form": form})


@login_required
def report_complaint(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not _booking_participant(booking, request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.booking = booking
            complaint.reported_by = request.user
            complaint.save()
            booking.status = "disputed"
            booking.save(update_fields=["status", "updated_at"])
            messages.success(request, "Report submitted for admin review.")
            return redirect("orders")
    else:
        form = ComplaintForm()
    return render(request, "rentals/complaint_form.html", {"form": form, "booking": booking})
