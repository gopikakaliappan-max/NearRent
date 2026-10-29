# NearRent — Nearby Product Rental Platform

NearRent is a Django-based web application that connects people who want to rent products with nearby product owners. It supports short-term product rentals, booking requests, delivery-cost sharing, product condition tracking, and communication between renters and owners.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Django
- **Database:** SQLite
- **Authentication:** Django built-in authentication
- **Image Handling:** Pillow
- **Static Files:** WhiteNoise
- **Version Control:** Git and GitHub
- **Deployment:** Render

## Key Features

1. **User Registration and Login** — Users can create accounts and sign in to the platform.
2. **Product Listings** — Owners can list products with descriptions, photos, rental prices, and condition details.
3. **Product Discovery** — Users can browse available rental products and search by relevant details.
4. **Location-Based Filtering** — Find products within a 10 km radius when valid coordinates are provided.
5. **Rental Booking** — Renters can submit booking requests for selected rental periods.
6. **Booking Management** — Owners and renters can view and manage their bookings.
7. **SplitFair Delivery** — Displays owner-arranged delivery costs and calculates an equal split by default.
8. **Private Booking Chat** — Enables communication between the renter and product owner for a booking.
9. **Rental Passport** — Booking-linked condition reports help document an item's condition before and after rental.
10. **Return Shield** — Both renter and owner confirm the return before the booking is marked completed.
11. **Wishlist** — Signed-in users can save products and view their saved listings.
12. **Ratings and Reviews** — Eligible renters can review products after completed bookings.
13. **Availability Calendar** — Owners can block unavailable dates to help prevent conflicting bookings.
14. **Rental Extensions and Cancellations** — Booking participants can request extensions or cancellations.
15. **Promo Codes** — Administrators can configure eligible percentage discounts.
16. **Smart Price Suggestions** — Provides category-based average rental price suggestions.
17. **Owner Analytics** — Displays listing and booking statistics for owners.
18. **Saved Searches and Reminders** — Users can save search preferences and manage on-site reminders.
19. **Printable Rental Receipts** — Booking participants can print or save receipt pages as PDFs.
20. **Feedback and Complaint Reporting** — Supports feedback, contact messages, and reports for administrative review.
21. **Admin Management** — Django's admin panel supports application data management and staff review workflows.

## Custom Project Highlights

### Rental Passport
A booking-linked condition timeline helps renters and owners record an item's condition before and after rental.

### SplitFair Delivery
Displays owner-arranged delivery costs and calculates an equal cost split by default.

### Return Shield
Requires both the renter and owner to confirm the return before the booking is marked as completed.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/gopikakaliappan-max/NearRent.git
cd NearRent
```

### 2. Create and activate a virtual environment

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

The project uses SQLite. Django creates and manages the database file through migrations, so a separate database server is not required.

Check `nearrent/settings.py` to confirm that the database engine is configured as:

```python
'ENGINE': 'django.db.backends.sqlite3',
```

### 5. Apply migrations

Run these commands from the folder containing `manage.py`:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

Skip this step if you already have an administrator account.

### 7. Start the development server

```bash
python manage.py runserver
```

Open the website at:

http://127.0.0.1:8000/

The Django admin panel is available at:

http://127.0.0.1:8000/admin/

## Live Deployment

**Live Website:** https://nearrent.onrender.com

**GitHub Repository:** https://github.com/gopikakaliappan-max/NearRent

The live website hostname above is an example based on the earlier deployment configuration. Replace it with the exact URL displayed in your Render Dashboard if it differs.

## Prototype Limitations

- Payment records are simulated. The application does not process real payments, security deposits, or refunds.
- The 10 km filter requires the renter and listings to have valid latitude and longitude coordinates.
- The prototype does not automatically obtain browser GPS coordinates or convert addresses into coordinates.
- Chat uses HTTP polling rather than WebSockets.
- Profile verification is a staff-managed review process, not official identity verification.
- Reminders appear within the application; automatic email, SMS, and push notifications are not implemented.
- Price suggestions use a simple category average, not machine learning.
- Printable receipts are not proof of payment.
- Email/mobile OTP verification and payment gateway integration are not fully implemented.
- Additional security, privacy, upload validation, and operational review are needed before real commercial use.

## Security Notes

- Keep `DEBUG=False` in production.
- Use a strong, randomly generated Django `SECRET_KEY` stored in environment variables.
- Configure `ALLOWED_HOSTS` for the deployed domain.
- Use HTTPS for public deployment.
- Never commit passwords, secret keys, or private credentials to GitHub.
- Back up your local database before applying significant model changes.

## Project Objective

NearRent aims to make short-term product rentals convenient by connecting nearby owners with people who need items temporarily. The platform encourages product reuse, reduces unnecessary purchases, and provides booking, communication, and condition-tracking workflows in one place.
