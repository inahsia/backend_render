"""
Test Email Configuration
Run this script to verify Gmail SMTP is working correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("=" * 60)
print("Testing Email Configuration")
print("=" * 60)
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"Email TLS: {settings.EMAIL_USE_TLS}")
print(f"Email User: {settings.EMAIL_HOST_USER}")
print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
print("=" * 60)

# Get recipient email
recipient = input("\nEnter recipient email address (to receive test email): ").strip()

if not recipient:
    print("✗ No recipient email provided. Exiting.")
    exit(1)

try:
    send_mail(
        subject='Test Email - Red Ball Cricket Academy',
        message='This is a test email. If you receive this, Gmail SMTP is configured correctly!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
    print(f"\n✓ Test email sent successfully to {recipient}!")
    print("✓ Check your inbox (and spam folder)")
    
except Exception as e:
    print(f"\n✗ Failed to send email: {e}")
    print("\nCommon solutions:")
    print("1. Make sure you've set up Gmail App Password (see GMAIL_SMTP_SETUP.md)")
    print("2. Update EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env file")
    print("3. Enable 2-Factor Authentication on your Gmail account")
