"""
Admin configuration for Red Ball Cricket Academy
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Sport, TimeSlot, Booking, Player, CheckInLog, UserProfile, BookingConfiguration, BreakTime

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Admin for custom user model"""
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'is_active')}
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'created_at']
    list_filter = ['user_type', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_per_hour', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['sport', 'date', 'start_time', 'end_time', 'price', 'is_booked', 'max_players']
    list_filter = ['sport', 'is_booked', 'date']
    search_fields = ['sport__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'slot', 'payment_verified', 'is_cancelled', 'organizer_check_in_count', 'get_organizer_status', 'created_at']
    list_filter = ['payment_verified', 'is_cancelled', 'organizer_check_in_count', 'created_at']
    search_fields = ['user__email', 'payment_id', 'order_id']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'slot']
    
    def get_organizer_status(self, obj):
        """Display organizer check-in status"""
        if obj.organizer_check_in_count == 0:
            return "Registered"
        elif obj.organizer_check_in_count == 1:
            return "Checked In"
        else:
            return "Checked Out"
    get_organizer_status.short_description = "Organizer Status"


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'booking', 'check_in_count', 'get_status', 'created_at']
    list_filter = ['check_in_count', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['qr_code', 'created_at', 'last_check_in', 'last_check_out']
    raw_id_fields = ['booking', 'user']


@admin.register(CheckInLog)
class CheckInLogAdmin(admin.ModelAdmin):
    list_display = ['player', 'action', 'timestamp', 'location']
    list_filter = ['action', 'timestamp']
    search_fields = ['player__name', 'player__email']
    readonly_fields = ['timestamp']
    raw_id_fields = ['player']


@admin.register(BookingConfiguration)
class BookingConfigurationAdmin(admin.ModelAdmin):
    list_display = ['sport', 'opens_at', 'closes_at', 'slot_duration', 'advance_booking_days', 'is_active']
    list_filter = ['is_active', 'slot_duration', 'advance_booking_days']
    search_fields = ['sport__name']
    readonly_fields = ['created_at', 'updated_at', 'total_slots_per_day']
    raw_id_fields = ['sport']


@admin.register(BreakTime)
class BreakTimeAdmin(admin.ModelAdmin):
    list_display = ['sport', 'start_time', 'end_time', 'reason', 'applies_to_weekdays', 'applies_to_weekends', 'is_active']
    list_filter = ['is_active', 'applies_to_weekdays', 'applies_to_weekends']
    search_fields = ['sport__name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['sport']
