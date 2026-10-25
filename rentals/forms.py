from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Booking, Feedback, ContactMessage, ConditionReport, Complaint


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True, label="Your name")

    class Meta:
        model = User
        fields = ("username", "first_name", "email", "password1", "password2")


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["title", "description", "category", "photo", "replacement_value", "daily_rent",
                  "security_deposit", "condition_notes", "location_name", "latitude", "longitude"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "condition_notes": forms.TextInput(attrs={"placeholder": "e.g. tiny scratch near clasp"}),
            "location_name": forms.TextInput(attrs={"placeholder": "e.g. Peelamedu, Coimbatore"}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["start_date", "end_date", "delivery_method", "delivery_total"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "delivery_total": forms.NumberInput(attrs={"min": "0", "step": "0.01", "id": "delivery-total"}),
        }

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        method = cleaned.get("delivery_method")
        fee = cleaned.get("delivery_total")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after the start date.")
        if method == "pickup":
            cleaned["delivery_total"] = 0
        if fee is not None and fee < 0:
            self.add_error("delivery_total", "Delivery cost cannot be negative.")
        return cleaned


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["rating", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us what went well or what we can improve..."})}


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}


class ConditionReportForm(forms.ModelForm):
    class Meta:
        model = ConditionReport
        fields = ["stage", "photo", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Describe the item condition clearly..."})}


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["category", "details"]
        widgets = {"details": forms.Textarea(attrs={"rows": 4})}
