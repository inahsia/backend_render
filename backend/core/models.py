"""
Models for Red Ball Cricket Academy Management System
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import json
from django.conf import settings
from django.core.mail import send_mail
try:
    # Optional Celery task for async emails; fallback to direct send if unavailable
    from .tasks import send_player_credentials_email  # type: ignore
except Exception:
    send_player_credentials_email = None
try:
    from .tasks import send_player_credentials_email
except Exception:
    send_player_credentials_email = None


class CustomUserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User model that uses email as the username field.
    Inherits from AbstractUser to maintain compatibility with existing Django auth.
    """
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    qr_token = models.CharField(max_length=512, blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/users/', blank=True, null=True)
    is_in = models.BooleanField(default=False)  # Track if user is checked in
    check_in_count = models.IntegerField(default=0)  # 0=registered, 1=in, 2=out
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already the USERNAME_FIELD
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email
    
    def generate_qr_code(self):
        """Generate QR code and token for user"""
        from django.core import signing
        
        # Create token with user info
        payload = {
            'user_id': self.id,
            'email': self.email,
            'ts': timezone.now().isoformat()
        }
        token = signing.dumps(payload, salt='user-qr-token')
        self.qr_token = token
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(token)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save to ImageField
        filename = f'user_{self.id}_qr.png'
        self.qr_code.save(filename, File(buffer), save=False)
        
        return token
class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('player', 'Player'),
    )
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} ({self.user_type})"

# Automatically create or update UserProfile when User is saved
@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Only save profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()

# Automatically generate QR code for users
@receiver(post_save, sender=CustomUser)
def ensure_user_qr_code(sender, instance, created, **kwargs):
    """Ensure every user has a QR code and token"""
    if not instance.qr_token:
        instance.generate_qr_code()
        instance.save()

from django.core.validators import MinValueValidator
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import json


class Sport(models.Model):
    """Sports offered by the academy"""
    name = models.CharField(max_length=100, unique=True)
    price_per_hour = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(default=60, validators=[MinValueValidator(1)], help_text="Duration in minutes")
    max_players = models.IntegerField(default=10, validators=[MinValueValidator(1)], help_text="Maximum number of players")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Sport'
        verbose_name_plural = 'Sports'

    def __str__(self):
        return f"{self.name} - ₹{self.price_per_hour}/hour"


class BookingConfiguration(models.Model):
    """Booking configuration for each sport"""
    SLOT_DURATION_CHOICES = [
        (30, '30 minutes'),
        (60, '1 hour'),
        (120, '2 hours'),
        (240, '4 hours'),
    ]
    
    ADVANCE_BOOKING_CHOICES = [
        (1, '1 day'),
        (3, '3 days'),
        (7, '7 days'),
        (15, '15 days'),
        (30, '30 days'),
    ]
    
    sport = models.OneToOneField(Sport, on_delete=models.CASCADE, related_name='booking_config')
    opens_at = models.TimeField(default='06:00')
    closes_at = models.TimeField(default='22:00')
    slot_duration = models.IntegerField(choices=SLOT_DURATION_CHOICES, default=60)
    advance_booking_days = models.IntegerField(choices=ADVANCE_BOOKING_CHOICES, default=7)
    min_booking_duration = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    max_booking_duration = models.IntegerField(default=4, validators=[MinValueValidator(1)])
    buffer_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Buffer time in minutes")
    
    # Weekend settings
    different_weekend_timings = models.BooleanField(default=False)
    weekend_opens_at = models.TimeField(null=True, blank=True)
    weekend_closes_at = models.TimeField(null=True, blank=True)
    
    # Pricing settings
    peak_hour_pricing = models.BooleanField(default=False)
    peak_start_time = models.TimeField(null=True, blank=True)
    peak_end_time = models.TimeField(null=True, blank=True)
    peak_price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    weekend_pricing = models.BooleanField(default=False)
    weekend_price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Booking Configuration'
        verbose_name_plural = 'Booking Configurations'
    
    def __str__(self):
        return f"Config for {self.sport.name}"
    
    @property
    def total_slots_per_day(self):
        """Calculate total slots per day"""
        from datetime import datetime, timedelta
        opens = datetime.combine(datetime.today(), self.opens_at)
        closes = datetime.combine(datetime.today(), self.closes_at)
        duration_minutes = self.slot_duration + self.buffer_time
        total_minutes = (closes - opens).total_seconds() / 60
        return int(total_minutes // duration_minutes) if duration_minutes > 0 else 0


class BreakTime(models.Model):
    """Break times when slots cannot be booked"""
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='break_times')
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(max_length=255, default='Break')
    applies_to_weekdays = models.BooleanField(default=True)
    applies_to_weekends = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Break Time'
        verbose_name_plural = 'Break Times'
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.sport.name} - {self.start_time} to {self.end_time}"


class BlackoutDate(models.Model):
    """Dates when a sport is completely unavailable"""
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='blackout_dates')
    date = models.DateField()
    reason = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Blackout Date'
        verbose_name_plural = 'Blackout Dates'
        ordering = ['date']
        unique_together = ['sport', 'date']
    
    def __str__(self):
        return f"{self.sport.name} - {self.date} ({self.reason})"


class TimeSlot(models.Model):
    """Time slots for booking"""
    sport = models.ForeignKey(
        Sport, 
        on_delete=models.CASCADE, 
        related_name='slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_booked = models.BooleanField(default=False)
    max_players = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    # Note: We'll use a separate field or model to track admin-disabled slots
    admin_disabled = models.BooleanField(default=False)  # Admin can disable slots
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['sport', 'date', 'start_time']
        verbose_name = 'Time Slot'
        verbose_name_plural = 'Time Slots'

    def __str__(self):
        return f"{self.sport.name} - {self.date} ({self.start_time} - {self.end_time})"

    def is_available(self):
        """Check if slot is available for booking"""
        # Check basic availability conditions
        if self.is_booked or self.admin_disabled or self.date < timezone.now().date():
            return False
        
        # Check if there's an active blackout date for this sport and date
        if BlackoutDate.objects.filter(
            sport=self.sport,
            date=self.date,
            is_active=True
        ).exists():
            return False
        
        return True


class Booking(models.Model):
    """Booking made by users"""
    user = models.ForeignKey(
        'CustomUser', 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    slot = models.OneToOneField(
        TimeSlot, 
        on_delete=models.CASCADE, 
        related_name='booking'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_verified = models.BooleanField(default=False)
    qr_token = models.CharField(max_length=512, blank=True, null=True)
    # Organizer (User) QR fields for this specific booking
    organizer_qr_token = models.CharField(max_length=512, blank=True, null=True)
    organizer_qr_code = models.ImageField(upload_to='qr_codes/organizers/', blank=True, null=True)
    organizer_is_in = models.BooleanField(default=False)  # Organizer check-in status for THIS booking
    organizer_check_in_count = models.IntegerField(default=0)  # 0=registered, 1=in, 2=out
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.CharField(max_length=255, blank=True, null=True)
    amount_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    def save(self, *args, **kwargs):
        # Automatically update status based on payment_verified and cancellation
        # Check cancellation first - cancelled bookings should stay cancelled
        if self.is_cancelled:
            self.status = 'cancelled'
            # Free up the slot when booking is cancelled
            if self.slot and self.slot.is_booked:
                self.slot.is_booked = False
                self.slot.save()
        elif self.payment_verified:
            self.status = 'confirmed'
        else:
            self.status = 'pending'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"Booking #{self.id} - {self.user.email} - {self.slot}"

    def generate_organizer_qr_code(self):
        """Generate QR code for the organizer (user) for this specific booking"""
        from django.core import signing
        
        payload = {
            'booking_id': self.id,
            'user_id': self.user.id,
            'type': 'organizer',
            'slot_date': str(self.slot.date),
            'sport': self.slot.sport.name if self.slot and self.slot.sport else 'Sport',
            'ts': timezone.now().isoformat()
        }
        token = signing.dumps(payload, salt='organizer-qr-token')
        self.organizer_qr_token = token
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(token)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save to ImageField
        filename = f'organizer_booking_{self.id}_qr.png'
        self.organizer_qr_code.save(filename, File(buffer), save=False)
        
        return token

    def cancel_booking(self, reason=""):
        """Cancel the booking"""
        self.is_cancelled = True
        self.cancellation_reason = reason
        self.slot.is_booked = False
        self.slot.save()
        self.save()


class Player(models.Model):
    """Players associated with a booking"""
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='players'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    user = models.ForeignKey(
        'CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='player_profiles'  # Changed to plural
    )
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_token = models.CharField(max_length=512, blank=True, null=True)
    check_in_count = models.IntegerField(default=0)
    is_in = models.BooleanField(default=False)  # Track if player is currently checked in
    last_check_in = models.DateTimeField(null=True, blank=True)
    last_check_out = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Player'
        verbose_name_plural = 'Players'

    def __str__(self):
        return f"{self.name} ({self.email})"

    def generate_qr_code(self):
        """Generate QR code with a signed token payload"""
        from django.core import signing
        payload = {
            'player_id': self.id,
            'booking_id': self.booking.id,
            'ts': timezone.now().isoformat(),
        }
        # Signed (tamper-proof) token
        token = signing.dumps(payload, salt='player-qr-token')
        self.qr_token = token

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # Encode only the token in the QR image
        qr.add_data(token)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save to model
        filename = f'player_{self.id}_qr.png'
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()

    def can_check_in(self):
        """Check if player can check in today"""
        booking_date = self.booking.slot.date
        today = timezone.now().date()
        return booking_date == today and self.check_in_count < 2

    def check_in(self):
        """Mark player as checked in/out"""
        if self.can_check_in():
            self.check_in_count += 1
            if self.check_in_count == 1:
                # First scan - Check IN
                self.last_check_in = timezone.now()
                self.is_in = True
            elif self.check_in_count == 2:
                # Second scan - Check OUT
                self.last_check_out = timezone.now()
                self.is_in = False
            self.save()
            return True
        return False

    def get_status(self):
        """Get current check-in status"""
        if self.check_in_count == 0:
            return "Registered"
        elif self.check_in_count == 1:
            return "Checked In"
        else:
            return "Checked Out"


class CheckInLog(models.Model):
    """Log of check-in/check-out activities"""
    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE, 
        related_name='check_logs'
    )
    action = models.CharField(
        max_length=10,
        choices=[('IN', 'Check In'), ('OUT', 'Check Out')]
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Check-In Log'
        verbose_name_plural = 'Check-In Logs'

    def __str__(self):
        return f"{self.player.name} - {self.action} at {self.timestamp}"


class UserCheckInLog(models.Model):
    """Log of user check-ins and check-outs"""
    ACTION_CHOICES = (
        ('IN', 'Check In'),
        ('OUT', 'Check Out'),
    )
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='checkin_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=3, choices=ACTION_CHOICES)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"


class OrganizerCheckInLog(models.Model):
    """Log of organizer check-ins and check-outs for specific bookings"""
    ACTION_CHOICES = (
        ('IN', 'Check In'),
        ('OUT', 'Check Out'),
    )
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='organizer_checkin_logs')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=3, choices=ACTION_CHOICES)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Booking #{self.booking.id} Organizer - {self.action} at {self.timestamp}"


# Automatically generate organizer QR when booking is confirmed
@receiver(post_save, sender=Booking)
def generate_organizer_qr_on_booking_confirm(sender, instance: Booking, created, **kwargs):
    """Generate organizer QR code when booking is payment verified"""
    if instance.payment_verified and not instance.organizer_qr_token:
        try:
            instance.generate_organizer_qr_code()
            instance.save(update_fields=['organizer_qr_token', 'organizer_qr_code'])
        except Exception as e:
            print(f"Failed to generate organizer QR for booking {instance.id}: {e}")


# Automatically handle Player creation side-effects
@receiver(post_save, sender=Player)
def ensure_player_account_qr_and_email(sender, instance: Player, created, **kwargs):
    """On Player create:
    - Create/attach a CustomUser with default password 'redball' if missing
    - Ensure profile.user_type = 'player'
    - Generate QR code if not present
    - Email credentials and booking details
    """
    if not created:
        return

    player = instance

    # 1) Create/attach user account
    user = player.user
    if not user and player.email:
        # Try to find existing user by email
        user = CustomUser.objects.filter(email__iexact=player.email).first()
        if not user:
            user = CustomUser.objects.create_user(
                email=player.email,
                password='redball',
                first_name=player.name,
            )
        # Mark as player and attach
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.user_type != 'player':
            profile.user_type = 'player'
            profile.save()
        # Save relation
        player.user = user
        player.save(update_fields=['user'])

    # 2) Generate QR code if missing
    if not player.qr_token:
        try:
            player.generate_qr_code()
            player.save(update_fields=['qr_token', 'qr_code'])
        except Exception as e:
            print(f"Failed to generate QR for player {player.id}: {e}")
            pass

    # 3) Email credentials (best-effort). Prefer Celery if available
    try:
        booking = player.booking
        slot = booking.slot if booking else None
        sport_name = slot.sport.name if slot else ''
        date_str = str(slot.date) if slot else ''
        time_window = f"{slot.start_time} - {slot.end_time}" if slot else ''
        if send_player_credentials_email:
            send_player_credentials_email.delay(player.email, player.name, sport_name, date_str, time_window)
        else:
            send_mail(
                subject='Your Player Account - Red Ball Cricket Academy',
                message=(
                    f"Hello {player.name},\n\n"
                    f"An account has been created for you at Red Ball Cricket Academy.\n\n"
                    f"Login Details:\n"
                    f"Email: {player.email}\n"
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
                recipient_list=[player.email] if player.email else [],
                fail_silently=True,
            )
    except Exception:
        pass


# Automatically generate QR code for new users
@receiver(post_save, sender=CustomUser)
def ensure_user_qr_code(sender, instance: CustomUser, created, **kwargs):
    """Generate QR code for newly created users"""
    if created and not instance.qr_token:
        try:
            instance.generate_qr_code()
            instance.save(update_fields=['qr_token', 'qr_code'])
        except Exception as e:
            print(f"Failed to generate QR for user {instance.id}: {e}")
            pass
