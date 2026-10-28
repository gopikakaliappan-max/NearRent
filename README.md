# NearRent — Django + MySQL starter project

NearRent is a student-project starter for a hyperlocal rental marketplace. It includes product listings, booking requests, shared delivery-cost calculations, booking-only private messaging, condition reports, return confirmations, feedback, contact form, terms page, and admin-managed complaints.

## Stack
- HTML, CSS, basic JavaScript
- Python + Django
- SQLite database 
- Django built-in authentication
- Image uploads for product and condition photos

## Three custom differentiators in this project
These are the project's chosen differentiators, not a claim that no other rental platform has similar features:
1. **Rental Passport:** a booking-linked before/after condition timeline.
2. **SplitFair delivery:** show the total owner-arranged delivery cost and split it equally by default.
3. **Return Shield:** both renter and owner confirm the return before the booking is marked completed.

## Important prototype limits
- Payment records are simulated. No real payments, deposits, or refunds are processed.
- The 10 km radius filter works when the renter enters latitude/longitude and listings have coordinates. The prototype does not automatically read browser GPS or geocode addresses; add consent-based geolocation or a geocoding provider if needed.
- Chat uses short-interval HTTP polling (not WebSockets). Only the renter and listing owner can access a booking chat.
- Email/mobile verification, live geolocation, payment gateway, delivery partner integration, moderation tooling, and production deployment security are not fully implemented.
- Do not use this demo to handle real high-value products or real payment deposits without security, privacy, legal, and operational review.

## 1. Install Python dependencies
Use Python 3.11+ recommended.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Then:
```bash
pip install -r requirements.txt
```

## 2. Create the MySQL database
Start MySQL and run:

```sql
CREATE DATABASE nearrent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Set environment variables before starting Django.

Windows PowerShell:
```powershell
$env:DB_NAME="nearrent_db"
$env:DB_USER="root"
$env:DB_PASSWORD="your_mysql_password"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
$env:SECRET_KEY="replace-with-a-long-random-secret"
$env:DEBUG="True"
```

macOS/Linux:
```bash
export DB_NAME=nearrent_db
export DB_USER=root
export DB_PASSWORD='your_mysql_password'
export DB_HOST=127.0.0.1
export DB_PORT=3306
export SECRET_KEY='replace-with-a-long-random-secret'
export DEBUG=True
```

You can copy `.env.example` as a reference, but the starter does not auto-load `.env`; export the variables in your terminal or add `python-dotenv` and configure it.

## 3. Create tables and admin account
From the folder containing `manage.py`:

```bash
python manage.py makemigrations rentals
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- Website: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## 4. Suggested demo steps
1. Register two accounts (one will list an item, the other will rent).
2. Log in as owner and list a product. Use a neighbourhood name, not a public home address.
3. Log in as renter and submit a rental request.
4. Switch back to owner and accept the request in Orders.
5. Open the booking chat from either account and exchange messages.
6. Owner confirms handover.
7. Both parties add condition reports from the booking.
8. Start return review and have each participant confirm the return.
9. Check the final booking status and estimated deposit refund.

## 5. Security and product notes
- `DEBUG=True` is for local development only. Set `DEBUG=False` and configure secure settings before deployment.
- Use HTTPS in production.
- Use least-privilege database credentials instead of the MySQL root account for deployment.
- Review upload size/type validation and malware handling before accepting public uploads.
- The current sample does not implement email/mobile OTP verification.
- Never store passwords in custom fields or logs.
- The terms page is a starter template, not legal advice.

## NearRent Feature Pack — 13 working features

This version includes the following implemented feature workflows in the Django app (not merely a list of ideas):

1. **Wishlist** — signed-in users can save/remove listings and view saved items.
2. **Verified profiles** — users submit a profile review request; staff can review and change status in Django admin. This is manual review, not government-ID verification.
3. **Product ratings and reviews** — a renter can review a completed booking once; reviews appear on the listing.
4. **Availability calendar** — owners can block/unblock unavailable dates; booking requests that overlap blocked dates are rejected.
5. **Rental extension requests** — a booking participant requests a later end date; the other participant can approve/decline, and conflicting dates are checked.
6. **Cancellation workflow** — either participant requests cancellation; the other can approve/decline. No real refund is processed.
7. **Promo codes** — admins create active percentage discounts with optional expiry and usage limits; valid codes can be applied during booking.
8. **Smart price suggestions** — owners see the average daily rent of other available listings in the same category.
9. **Owner analytics** — each owner sees listing count, booking count, completed bookings, tracked rental value, wishlist saves, and listing booking counts.
10. **Saved searches** — users can save a query/category and reopen that search.
11. **Booking reminders** — users can create and mark reminders done. The prototype displays them on the site; it does not send push/email alerts automatically.
12. **Printable rental receipt** — participants can print or save an HTML receipt as PDF from the browser. It is not proof of payment.
13. **Suspicious listing reports** — signed-in users can report another user's listing for admin review; a report does not automatically remove the listing.

### Apply database changes

The added features introduce new models and fields. From the folder containing `manage.py`, run:

```bash
python manage.py makemigrations rentals
python manage.py migrate
python manage.py check
python manage.py createsuperuser  # only if you do not already have an admin account
python manage.py runserver
```

Use the existing database settings in `.env.example` / `nearrent/settings.py`. **Back up your existing database before applying migrations** if you have real project data. Existing user accounts and passwords are not intentionally changed by these model additions.

### Where to find features

After login, the navigation bar includes Wishlist, Saved searches, Reminders, Analytics, and Verify profile. Product details provide wishlist, owner availability and price suggestion tools, plus a report link for non-owners. Booking cards provide printable receipts, extension requests, cancellation requests, and a review link after a completed booking. Promo codes are managed through Django admin.

### Prototype boundaries

- This is a student-project prototype, not a production-ready marketplace. Test each flow with two test accounts before presenting it.
- Profile verification is staff-managed and does not validate identity documents.
- Reminder records are shown in the app but no background scheduler or email/SMS/push delivery is included.
- Price suggestions use a simple category average, not machine learning.
- Receipts are printable HTML; no payment gateway or real payment processing is included.
- Run `makemigrations` and `migrate` before starting the updated project. The ZIP does not include your local database or secrets.
