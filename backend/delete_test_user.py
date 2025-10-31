"""
Delete test user so they can register again
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

email = 'singhaishani2003@gmail.com'

print(f'Looking for user with email: {email}')

user = User.objects.filter(email=email).first()

if user:
    print(f'\nFound user:')
    print(f'  ID: {user.id}')
    print(f'  Email: {user.email}')
    print(f'  Name: {user.first_name} {user.last_name}')
    print(f'  Staff: {user.is_staff}')
    print(f'  Active: {user.is_active}')
    
    response = input('\n⚠️  Delete this user? (type YES to confirm): ')
    
    if response == 'YES':
        # First delete related objects manually to avoid the FK error
        try:
            # Delete bookings (this will cascade to players)
            from core.models import Booking
            bookings = Booking.objects.filter(user=user)
            booking_count = bookings.count()
            if booking_count > 0:
                print(f'\n🧹 Deleting {booking_count} bookings...')
                bookings.delete()
                print('   ✅ Bookings deleted')
            
            # Now delete user
            print(f'\n🗑️  Deleting user {email}...')
            user.delete()
            print('✅ User deleted successfully!')
            print('\nYou can now register with this email again.')
            
        except Exception as e:
            print(f'❌ Error deleting user: {str(e)}')
            import traceback
            traceback.print_exc()
    else:
        print('Cancelled. User not deleted.')
else:
    print(f'✅ User not found. Email {email} is available for registration.')
