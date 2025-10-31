import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Booking

today = date.today()

print(f"Organizer QR tokens for bookings on {today}:")
for booking in Booking.objects.filter(slot__date=today):
    print(f"Booking ID: {booking.id}")
    print(f"Organizer QR Token: {booking.organizer_qr_token}")
    print(f"Check-in Count: {booking.organizer_check_in_count}")
    print(f"Is In: {booking.organizer_is_in}")
    print('-' * 40)
