# Red Ball Cricket Academy - Backend Setup Guide

## Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip

## Installation Steps

### 1. Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup PostgreSQL Database
Create a database named `redball_cricket_db`:
```sql
CREATE DATABASE redball_cricket_db;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE redball_cricket_db TO postgres;
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and update with your values:
```bash
copy .env.example .env
```

Edit `.env` file:
```
DEBUG=True
SECRET_KEY=your-django-secret-key
DATABASE_NAME=redball_cricket_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user

### Sports
- `GET /api/sports/` - List all sports
- `POST /api/sports/` - Create sport (Admin)
- `GET /api/sports/{id}/` - Get sport details
- `PUT /api/sports/{id}/` - Update sport (Admin)
- `DELETE /api/sports/{id}/` - Delete sport (Admin)
- `GET /api/sports/{id}/available_slots/` - Get available slots for sport

### Slots
- `GET /api/slots/` - List all slots
  - Query params: `?sport=1&date=2025-10-20&available=true`
- `POST /api/slots/` - Create slot (Admin)
- `POST /api/slots/bulk_create/` - Create multiple slots (Admin)
- `GET /api/slots/{id}/` - Get slot details
- `PUT /api/slots/{id}/` - Update slot (Admin)
- `DELETE /api/slots/{id}/` - Delete slot (Admin)

### Bookings
- `GET /api/bookings/` - List user's bookings
- `POST /api/bookings/` - Create new booking
- `GET /api/bookings/{id}/` - Get booking details
- `POST /api/bookings/{id}/cancel/` - Cancel booking
- `GET /api/bookings/{id}/players/` - Get players for booking

### Players
- `GET /api/players/` - List players
- `POST /api/players/` - Add player to booking
- `GET /api/players/{id}/` - Get player details
- `GET /api/players/{id}/qr_code/` - Get player QR code
- `POST /api/players/scan_qr/` - Scan QR for check-in/out

### Payments
- `POST /api/payments/create-order/` - Create Razorpay order
- `POST /api/payments/verify/` - Verify payment

### Dashboard
- `GET /api/dashboard/stats/` - Get dashboard statistics (Admin)

## API Documentation
- Swagger UI: `http://127.0.0.1:8000/swagger/`
- ReDoc: `http://127.0.0.1:8000/redoc/`

## Admin Panel
Access Django admin at: `http://127.0.0.1:8000/admin/`

## Features

### Admin Features
- Add, edit, delete sports and slots
- Set slot timings and prices
- View all bookings and players
- Cancel or change bookings
- View dashboard statistics

### User Features
- Register and login
- View available sports and slots
- Book slots
- Make payments via Razorpay
- Add players to bookings
- View booking history

### Player Features
- Login with email and password "redball"
- View assigned booking
- Access QR code (valid only on booking date)
- QR code scanning for check-in/out

## QR Code System
- Each player gets a unique QR code after being added to a booking
- QR code contains: player_id, booking_id, date, name, email
- First scan: Check IN
- Second scan: Check OUT
- QR code is valid only on the booking date

## Testing
```bash
python manage.py test
```

## Production Deployment
1. Set `DEBUG=False` in `.env`
2. Update `ALLOWED_HOSTS` in settings.py
3. Configure static files serving
4. Use a production-grade WSGI server (gunicorn)
5. Set up SSL certificate
6. Configure CORS properly for your frontend domain

## Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists

### Import Errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Migration Issues
```bash
python manage.py makemigrations --empty core
python manage.py migrate --run-syncdb
```

## Support
For issues and questions, contact: admin@redballcricket.com
# academy-final-backend-
