from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_player_credentials_email(email, name, sport_name, date_str, time_window):
    try:
        send_mail(
            subject='Your Player Account - Red Ball Cricket Academy',
            message=(
                f"Hello {name},\n\n"
                f"An account has been created for you at Red Ball Cricket Academy.\n\n"
                f"Login Details:\n"
                f"Email: {email}\n"
                f"Temporary Password: redball\n\n"
                f"Booking Details:\n"
                f"Sport: {sport_name}\n"
                f"Date: {date_str}\n"
                f"Time: {time_window}\n\n"
                f"Use the app to view your QR code and check-in on the day of your booking.\n"
                f"For security, please change your password after first login.\n\n"
                f"Regards,\nRed Ball Cricket Academy"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        # Best effort; do not raise to Celery
        pass
