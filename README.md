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
