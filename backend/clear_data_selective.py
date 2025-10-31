"""
Selective data cleanup script
Choose what data to keep or remove for testing
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

def display_current_data():
    """Display current database statistics"""
    print("\n📊 Current Database Statistics:")
    print("="*70)
    print(f"   Sports: {Sport.objects.count()}")
    print(f"   Time Slots: {TimeSlot.objects.count()}")
    print(f"   Bookings: {Booking.objects.count()}")
    print(f"   Players: {Player.objects.count()}")
    print(f"   Regular Users: {User.objects.filter(is_superuser=False).count()}")
    print(f"   Admin Users: {User.objects.filter(is_superuser=True).count()}")
    print(f"   Organizer Check-in Logs: {OrganizerCheckInLog.objects.count()}")
    print(f"   Player Check-in Logs: {CheckInLog.objects.count()}")
    print(f"   Booking Configurations: {BookingConfiguration.objects.count()}")
    print(f"   Break Times: {BreakTime.objects.count()}")
    print(f"   Blackout Dates: {BlackoutDate.objects.count()}")
    print("="*70)

def clear_bookings_and_players():
    """Clear only bookings, players, and related logs"""
    logs = OrganizerCheckInLog.objects.count()
    player_logs = CheckInLog.objects.count()
    players = Player.objects.count()
    bookings = Booking.objects.count()
    
    OrganizerCheckInLog.objects.all().delete()
    CheckInLog.objects.all().delete()
    Player.objects.all().delete()
    Booking.objects.all().delete()
    
    print(f"\n✅ Cleared:")
    print(f"   • {logs} organizer check-in logs")
    print(f"   • {player_logs} player check-in logs")
    print(f"   • {players} players")
    print(f"   • {bookings} bookings")
    print("\n✓ Sports and time slots are preserved")

def clear_time_slots():
    """Clear only time slots (will also clear bookings)"""
    bookings = Booking.objects.count()
    Booking.objects.all().delete()
    
    slots = TimeSlot.objects.count()
    TimeSlot.objects.all().delete()
    
    print(f"\n✅ Cleared:")
    print(f"   • {slots} time slots")
    print(f"   • {bookings} bookings (cascade)")
    print("\n✓ Sports are preserved")

def clear_sports():
    """Clear sports and everything dependent on them"""
    bookings = Booking.objects.count()
    Booking.objects.all().delete()
    
    slots = TimeSlot.objects.count()
    TimeSlot.objects.all().delete()
    
    configs = BookingConfiguration.objects.count()
    BookingConfiguration.objects.all().delete()
    
    breaks = BreakTime.objects.count()
    BreakTime.objects.all().delete()
    
    blackouts = BlackoutDate.objects.count()
    BlackoutDate.objects.all().delete()
    
    sports = Sport.objects.count()
    Sport.objects.all().delete()
    
    print(f"\n✅ Cleared:")
    print(f"   • {sports} sports")
    print(f"   • {slots} time slots")
    print(f"   • {bookings} bookings")
    print(f"   • {configs} configurations")
    print(f"   • {breaks} break times")
    print(f"   • {blackouts} blackout dates")

def clear_users():
    """Clear only regular users (preserve admins)"""
    users = User.objects.filter(is_superuser=False)
    count = users.count()
    users.delete()
    
    print(f"\n✅ Cleared {count} regular users")
    print(f"✓ Admin users preserved")

def main():
    print("\n" + "="*70)
    print("🧹 SELECTIVE DATABASE CLEANUP")
    print("="*70)
    
    display_current_data()
    
    print("\n📋 Cleanup Options:")
    print("="*70)
    print("1. Clear bookings and players only (keep sports, slots, users)")
    print("2. Clear time slots (will also clear bookings)")
    print("3. Clear sports (will clear everything dependent on sports)")
    print("4. Clear regular users only (preserve admins)")
    print("5. Clear EVERYTHING except admin users")
    print("6. Cancel and exit")
    print("="*70)
    
    choice = input("\n👉 Enter your choice (1-6): ").strip()
    
    if choice == '6':
        print("\n❌ Operation cancelled.")
        return
    
    confirm = input("\n⚠️  Type 'YES' to confirm: ")
    if confirm != 'YES':
        print("\n❌ Operation cancelled.")
        return
    
    print("\n🗑️  Processing...")
    
    try:
        if choice == '1':
            clear_bookings_and_players()
        elif choice == '2':
            clear_time_slots()
        elif choice == '3':
            clear_sports()
        elif choice == '4':
            clear_users()
        elif choice == '5':
            # Clear everything
            OrganizerCheckInLog.objects.all().delete()
            CheckInLog.objects.all().delete()
            Player.objects.all().delete()
            Booking.objects.all().delete()
            TimeSlot.objects.all().delete()
            BookingConfiguration.objects.all().delete()
            BreakTime.objects.all().delete()
            BlackoutDate.objects.all().delete()
            Sport.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            print("\n✅ All data cleared (admin users preserved)")
        else:
            print("\n❌ Invalid choice")
            return
        
        print("\n" + "="*70)
        print("✅ CLEANUP COMPLETED!")
        print("="*70)
        
        display_current_data()
        
        print("\n🎯 Database is ready for testing!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
