"""
Clear all data from database tables for fresh testing
This will delete all records but keep the table structure intact
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import (
    Sport, TimeSlot, Booking, Player, CheckInLog,
    BookingConfiguration, BreakTime, BlackoutDate,
    OrganizerCheckInLog
)

User = get_user_model()

def clear_all_data():
    """Clear all data from database tables"""
    print("\n" + "="*70)
    print("⚠️  DATABASE DATA CLEANUP")
    print("="*70)
    
    # Confirm action
    print("\n🚨 WARNING: This will DELETE ALL DATA from your database!")
    print("   - All bookings will be removed")
    print("   - All players will be removed")
    print("   - All time slots will be removed")
    print("   - All sports will be removed")
    print("   - All users (except superusers) will be removed")
    print("   - All configurations will be removed")
    
    confirm = input("\n⚠️  Are you ABSOLUTELY SURE? Type 'YES' to continue: ")
    
    if confirm != 'YES':
        print("\n❌ Operation cancelled. No data was deleted.")
        return
    
    print("\n🗑️  Starting data cleanup...\n")
    
    try:
        # Delete in order to respect foreign key constraints
        
        # 1. Delete check-in logs first
        organizer_logs_count = OrganizerCheckInLog.objects.count()
        OrganizerCheckInLog.objects.all().delete()
        print(f"✓ Deleted {organizer_logs_count} organizer check-in logs")
        
        player_logs_count = CheckInLog.objects.count()
        CheckInLog.objects.all().delete()
        print(f"✓ Deleted {player_logs_count} player check-in logs")
        
        # 2. Delete players
        players_count = Player.objects.count()
        Player.objects.all().delete()
        print(f"✓ Deleted {players_count} players")
        
        # 3. Delete bookings
        bookings_count = Booking.objects.count()
        Booking.objects.all().delete()
        print(f"✓ Deleted {bookings_count} bookings")
        
        # 4. Delete time slots
        slots_count = TimeSlot.objects.count()
        TimeSlot.objects.all().delete()
        print(f"✓ Deleted {slots_count} time slots")
        
        # 5. Delete configurations
        config_count = BookingConfiguration.objects.count()
        BookingConfiguration.objects.all().delete()
        print(f"✓ Deleted {config_count} booking configurations")
        
        break_count = BreakTime.objects.count()
        BreakTime.objects.all().delete()
        print(f"✓ Deleted {break_count} break times")
        
        blackout_count = BlackoutDate.objects.count()
        BlackoutDate.objects.all().delete()
        print(f"✓ Deleted {blackout_count} blackout dates")
        
        # 6. Delete sports
        sports_count = Sport.objects.count()
        Sport.objects.all().delete()
        print(f"✓ Deleted {sports_count} sports")
        
        # 7. Delete non-superuser users
        regular_users = User.objects.filter(is_superuser=False)
        users_count = regular_users.count()
        regular_users.delete()
        print(f"✓ Deleted {users_count} regular users (superusers preserved)")
        
        print("\n" + "="*70)
        print("✅ DATABASE CLEANUP COMPLETED!")
        print("="*70)
        print("\n📊 Summary:")
        print(f"   • {organizer_logs_count} organizer check-in logs removed")
        print(f"   • {player_logs_count} player check-in logs removed")
        print(f"   • {players_count} players removed")
        print(f"   • {bookings_count} bookings removed")
        print(f"   • {slots_count} time slots removed")
        print(f"   • {sports_count} sports removed")
        print(f"   • {users_count} regular users removed")
        print(f"   • {config_count} configurations removed")
        print(f"   • {break_count} break times removed")
        print(f"   • {blackout_count} blackout dates removed")
        
        # Show remaining superusers
        superusers = User.objects.filter(is_superuser=True)
        print(f"\n👨‍💼 Admin accounts preserved: {superusers.count()}")
        for admin in superusers:
            print(f"   • {admin.email} (username: {admin.username})")
        
        print("\n🎯 Your database is now clean and ready for fresh testing!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    clear_all_data()
