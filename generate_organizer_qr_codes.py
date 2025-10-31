"""
Generate organizer QR codes for all existing confirmed bookings
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Booking

def generate_organizer_qrs():
    """Generate organizer QR codes for all confirmed bookings without them"""
    bookings = Booking.objects.filter(
        payment_verified=True,
        is_cancelled=False,
        organizer_qr_token__isnull=True
    )
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for booking in bookings:
        try:
            if booking.organizer_qr_token:
                print(f"⏭️  Skipping booking #{booking.id} (already has QR)")
                skip_count += 1
                continue
            
            print(f"🔄 Generating organizer QR for booking #{booking.id} ({booking.slot.sport.name} - {booking.slot.date})")
            booking.generate_organizer_qr_code()
            booking.save()
            print(f"✅ Generated organizer QR for booking #{booking.id}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed for booking #{booking.id}: {str(e)}")
            fail_count += 1
    
    print("\n" + "="*50)
    print(f"✅ Success: {success_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print(f"❌ Failed: {fail_count}")
    print("="*50)
    
    if fail_count == 0 and success_count > 0:
        print("🎉 All confirmed bookings now have organizer QR codes!")

if __name__ == '__main__':
    generate_organizer_qrs()
