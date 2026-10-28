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
from .forms import RegisterForm, ProductForm, BookingForm, FeedbackForm, ContactForm, ConditionReportForm, ComplaintForm, ProfileVerificationForm, ReviewForm, AvailabilityForm, ExtensionRequestForm, CancellationRequestForm, SavedSearchForm, ReminderForm, ListingReportForm
from .models import Product, Booking, Message, Feedback, ContactMessage, ConditionReport, Complaint, Wishlist, UserProfile, ProductReview, ProductAvailability, ExtensionRequest, CancellationRequest, PromoCode, SavedSearch, BookingReminder, ListingReport


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
            blocked = ProductAvailability.objects.filter(product=product, date__gte=start, date__lte=end).exists()
            if blocked:
                form.add_error(None, "The owner marked one or more selected dates unavailable.")
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
                promo_text = form.cleaned_data.get("promo_code", "").strip().upper()
                if promo_text:
                    promo = PromoCode.objects.filter(code__iexact=promo_text).first()
                    if promo and promo.is_valid_now:
                        booking.discount_amount = (booking.agreed_rent * Decimal(promo.percent_off) / Decimal("100")).quantize(Decimal("0.01"))
                        booking.promo_code_used = promo.code
                        promo.uses += 1
                        promo.save(update_fields=["uses"])
                    else:
                        form.add_error("promo_code", "That promo code is invalid, expired, or fully used.")
                booking.agreed_rent = max(booking.agreed_rent - booking.discount_amount, Decimal("0.00"))
                booking.agreed_deposit = product.security_deposit
                booking.delivery_total = form.cleaned_data["delivery_total"] or Decimal("0.00")
                booking.renter_delivery_share = (booking.delivery_total / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                booking.owner_delivery_share = booking.delivery_total - booking.renter_delivery_share
                booking.renter_paid_amount = booking.agreed_rent + booking.agreed_deposit + booking.renter_delivery_share
                if form.errors:
                    return render(request, "rentals/booking_form.html", {"form": form, "product": product})
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

# --- 13 feature pack views ---
from datetime import timedelta
from django.db.models import Avg, Count, Sum
from django.http import HttpResponse
from django.utils.dateparse import parse_date

@login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product','product__owner')
    return render(request, 'rentals/feature_page.html', {'title':'My wishlist','items':items,'feature':'wishlist'})

@login_required
@require_POST
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created: item.delete(); messages.info(request, 'Removed from your wishlist.')
    else: messages.success(request, 'Saved to your wishlist.')
    return redirect(request.POST.get('next') or 'wishlist')

@login_required
def profile_verification(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileVerificationForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False); profile.verification_status = 'pending'; profile.save()
            messages.success(request, 'Verification request sent for admin review. No identity documents are collected in this demo.')
            return redirect('profile_verification')
    else: form = ProfileVerificationForm(instance=profile)
    return render(request, 'rentals/feature_page.html', {'title':'Profile verification','form':form,'profile':profile,'feature':'verification'})

@login_required
def product_review(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('product'), pk=pk, renter=request.user, status='completed')
    if ProductReview.objects.filter(booking=booking, reviewer=request.user).exists():
        messages.info(request, 'You already reviewed this booking.'); return redirect('product_detail', pk=booking.product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False); review.booking = booking; review.product = booking.product; review.reviewer = request.user; review.save()
            messages.success(request, 'Thank you for reviewing this rental.'); return redirect('product_detail', pk=booking.product_id)
    else: form = ReviewForm()
    return render(request, 'rentals/feature_page.html', {'title':'Review rental','form':form,'feature':'review'})

@login_required
def manage_availability(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False); entry.product = product
            try: entry.save(); messages.success(request, 'Unavailable date saved.')
            except Exception: messages.info(request, 'That date is already blocked.')
            return redirect('manage_availability', pk=pk)
    else: form = AvailabilityForm()
    dates = ProductAvailability.objects.filter(product=product)
    return render(request, 'rentals/feature_page.html', {'title':f'Availability: {product.title}','form':form,'items':dates,'product':product,'feature':'availability'})

@login_required
@require_POST
def delete_availability(request, pk, date_pk):
    entry = get_object_or_404(ProductAvailability, pk=date_pk, product__pk=pk, product__owner=request.user); entry.delete()
    messages.success(request, 'Blocked date removed.'); return redirect('manage_availability', pk=pk)

@login_required
def extension_request(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('product'), pk=pk)
    if not _booking_participant(booking, request.user): raise PermissionDenied
    if request.method == 'POST':
        form = ExtensionRequestForm(request.POST)
        if form.is_valid():
            proposed = form.cleaned_data['proposed_end_date']
            if proposed <= booking.end_date: form.add_error('proposed_end_date', 'Choose a date after the current end date.')
            elif booking.status not in ['accepted','active']: form.add_error(None, 'Only accepted or active bookings can be extended.')
            if not form.errors:
                item = form.save(commit=False); item.booking = booking; item.requested_by = request.user; item.save()
                messages.success(request, 'Extension request sent to the other participant.'); return redirect('orders')
    else: form = ExtensionRequestForm(initial={'proposed_end_date':booking.end_date + timedelta(days=1)})
    return render(request, 'rentals/feature_page.html', {'title':f'Extend booking #{booking.pk}','form':form,'booking':booking,'items':booking.extension_requests.all(),'feature':'extension'})

@login_required
@require_POST
def extension_decision(request, request_pk, decision):
    item = get_object_or_404(ExtensionRequest.objects.select_related('booking__product'), pk=request_pk, status='pending')
    if not _booking_participant(item.booking, request.user) or item.requested_by_id == request.user.id: raise PermissionDenied
    booking = item.booking
    if decision == 'approve' and item.proposed_end_date > booking.end_date:
        overlap = Booking.objects.filter(product=booking.product, status__in=['requested','accepted','active','return_review'], start_date__lte=item.proposed_end_date, end_date__gt=booking.end_date).exclude(pk=booking.pk).exists()
        if overlap: messages.error(request, 'Those dates conflict with another booking.'); return redirect('extension_request', pk=booking.pk)
        extra_days = (item.proposed_end_date - booking.end_date).days
        booking.end_date = item.proposed_end_date; booking.agreed_rent += booking.product.daily_rent * extra_days; booking.renter_paid_amount += booking.product.daily_rent * extra_days; booking.save()
        item.status = 'approved'; item.save(); messages.success(request, 'Extension approved and booking dates updated.')
    elif decision == 'decline': item.status='declined'; item.save(); messages.info(request, 'Extension declined.')
    else: messages.error(request, 'Invalid decision.')
    return redirect('orders')

@login_required
def cancellation_request(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not _booking_participant(booking, request.user): raise PermissionDenied
    if booking.status not in ['requested','accepted']: messages.error(request, 'This booking can no longer be cancelled through this workflow.'); return redirect('orders')
    if request.method == 'POST':
        form = CancellationRequestForm(request.POST)
        if form.is_valid():
            item=form.save(commit=False); item.booking=booking; item.requested_by=request.user; item.save()
            messages.success(request, 'Cancellation request sent to the other participant.'); return redirect('orders')
    else: form=CancellationRequestForm()
    return render(request, 'rentals/feature_page.html', {'title':f'Cancel booking #{booking.pk}','form':form,'booking':booking,'items':booking.cancellation_requests.all(),'feature':'cancellation'})

@login_required
@require_POST
def cancellation_decision(request, request_pk, decision):
    item=get_object_or_404(CancellationRequest.objects.select_related('booking__product'),pk=request_pk,status='pending')
    if not _booking_participant(item.booking,request.user) or item.requested_by_id==request.user.id: raise PermissionDenied
    if decision=='approve': item.status='approved'; item.booking.status='cancelled'; item.booking.save(update_fields=['status','updated_at']); messages.success(request,'Cancellation approved. Any money handling must be arranged outside this prototype.')
    elif decision=='decline': item.status='declined'; messages.info(request,'Cancellation declined.')
    else: messages.error(request,'Invalid decision.'); return redirect('orders')
    item.save(); return redirect('orders')

@login_required
def saved_searches(request):
    if request.method == 'POST':
        form=SavedSearchForm(request.POST)
        if form.is_valid():
            s=form.save(commit=False); s.user=request.user; s.save(); messages.success(request,'Search saved.'); return redirect('saved_searches')
    else: form=SavedSearchForm(initial={'query':request.GET.get('q',''),'category':request.GET.get('category','')})
    return render(request,'rentals/feature_page.html',{'title':'Saved searches','form':form,'items':SavedSearch.objects.filter(user=request.user),'feature':'saved_searches'})

@login_required
def reminders(request):
    if request.method == 'POST':
        form=ReminderForm(request.POST)
        if form.is_valid():
            r=form.save(commit=False); booking_id=request.POST.get('booking_id')
            r.booking=get_object_or_404(Booking,pk=booking_id) if booking_id else None
            if r.booking and not _booking_participant(r.booking,request.user): raise PermissionDenied
            r.user=request.user; r.save(); messages.success(request,'Reminder saved. This prototype displays reminders in your dashboard; it does not send push/email notifications.'); return redirect('reminders')
    else: form=ReminderForm()
    items=BookingReminder.objects.filter(user=request.user).select_related('booking').order_by('is_done','remind_on')
    return render(request,'rentals/feature_page.html',{'title':'Booking reminders','form':form,'items':items,'bookings':Booking.objects.filter(Q(renter=request.user)|Q(product__owner=request.user)).select_related('product'),'feature':'reminders'})

@login_required
@require_POST
def reminder_done(request, pk):
    item=get_object_or_404(BookingReminder,pk=pk,user=request.user); item.is_done=not item.is_done; item.save(update_fields=['is_done']); return redirect('reminders')

@login_required
def rental_receipt(request, pk):
    booking=get_object_or_404(Booking.objects.select_related('product','renter','product__owner'),pk=pk)
    if not _booking_participant(booking,request.user): raise PermissionDenied
    return render(request,'rentals/receipt.html',{'booking':booking,'print_mode':True})

@login_required
def report_listing(request, pk):
    product=get_object_or_404(Product,pk=pk)
    if product.owner_id==request.user.id: messages.error(request,'You cannot report your own listing.'); return redirect('product_detail',pk=pk)
    if request.method=='POST':
        form=ListingReportForm(request.POST)
        if form.is_valid():
            r=form.save(commit=False); r.product=product; r.reported_by=request.user; r.save(); messages.success(request,'Report sent to the site administrator for review.'); return redirect('product_detail',pk=pk)
    else: form=ListingReportForm()
    return render(request,'rentals/feature_page.html',{'title':f'Report listing: {product.title}','form':form,'product':product,'feature':'report'})

@login_required
def price_suggestion(request, pk):
    product=get_object_or_404(Product,pk=pk,owner=request.user)
    comparable=Product.objects.filter(category=product.category,is_available=True).exclude(pk=product.pk)
    average=comparable.aggregate(avg=Avg('daily_rent'))['avg']
    suggested=(average or product.daily_rent).quantize(Decimal('0.01'))
    return render(request,'rentals/feature_page.html',{'title':'Smart price suggestion','product':product,'suggested_price':suggested,'sample_size':comparable.count(),'feature':'pricing'})

@login_required
def owner_analytics(request):
    products=Product.objects.filter(owner=request.user)
    bookings=Booking.objects.filter(product__owner=request.user)
    summary={'listing_count':products.count(),'booking_count':bookings.count(),'completed_count':bookings.filter(status='completed').count(),'estimated_rent':bookings.filter(status__in=['completed','active','return_review']).aggregate(total=Sum('agreed_rent'))['total'] or Decimal('0.00'),'wishlist_count':Wishlist.objects.filter(product__owner=request.user).count()}
    top_products=products.annotate(booking_count=Count('bookings')).order_by('-booking_count')[:10]
    return render(request,'rentals/feature_page.html',{'title':'Owner analytics','summary':summary,'items':top_products,'feature':'analytics'})
