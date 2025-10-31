"""
Serializers for Red Ball Cricket Academy API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Sport, TimeSlot, Booking, Player, CheckInLog, BookingConfiguration, BreakTime, BlackoutDate

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'qr_token', 'qr_code', 'qr_code_url', 'is_in', 'check_in_count']
        read_only_fields = ['id', 'qr_token', 'qr_code', 'is_in', 'check_in_count']
    
    def get_qr_code_url(self, obj):
        """Get full URL for QR code image"""
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
        return None


class BookingConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for BookingConfiguration model"""
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    total_slots_per_day = serializers.ReadOnlyField()
    
    class Meta:
        model = BookingConfiguration
        fields = ['id', 'sport', 'sport_name', 'opens_at', 'closes_at', 'slot_duration', 
                  'advance_booking_days', 'min_booking_duration', 'max_booking_duration', 
                  'buffer_time', 'different_weekend_timings', 'weekend_opens_at', 'weekend_closes_at',
                  'peak_hour_pricing', 'peak_start_time', 'peak_end_time', 'peak_price_multiplier',
                  'weekend_pricing', 'weekend_price_multiplier', 'is_active', 'total_slots_per_day',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate booking configuration data"""
        # Convert decimal strings to Decimal
        from decimal import Decimal
        
        if 'peak_price_multiplier' in data and isinstance(data['peak_price_multiplier'], str):
            try:
                data['peak_price_multiplier'] = Decimal(data['peak_price_multiplier'])
            except (ValueError, TypeError):
                raise serializers.ValidationError({'peak_price_multiplier': 'Invalid decimal format'})
        
        if 'weekend_price_multiplier' in data and isinstance(data['weekend_price_multiplier'], str):
            try:
                data['weekend_price_multiplier'] = Decimal(data['weekend_price_multiplier'])
            except (ValueError, TypeError):
                raise serializers.ValidationError({'weekend_price_multiplier': 'Invalid decimal format'})
        
        # Validate weekend timings if enabled
        if data.get('different_weekend_timings'):
            if not data.get('weekend_opens_at') or not data.get('weekend_closes_at'):
                raise serializers.ValidationError(
                    'Weekend opening and closing times are required when different weekend timings is enabled'
                )
        
        # Validate peak hour pricing if enabled
        if data.get('peak_hour_pricing'):
            if not data.get('peak_start_time') or not data.get('peak_end_time'):
                raise serializers.ValidationError(
                    'Peak start and end times are required when peak hour pricing is enabled'
                )
        
        return data


class BreakTimeSerializer(serializers.ModelSerializer):
    """Serializer for BreakTime model"""
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    
    class Meta:
        model = BreakTime
        fields = ['id', 'sport', 'sport_name', 'start_time', 'end_time', 'reason',
                  'applies_to_weekdays', 'applies_to_weekends', 'is_active', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BlackoutDateSerializer(serializers.ModelSerializer):
    """Serializer for BlackoutDate model"""
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    
    class Meta:
        model = BlackoutDate
        fields = ['id', 'sport', 'sport_name', 'date', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class SportSerializer(serializers.ModelSerializer):
    """Serializer for Sport model"""
    available_slots_count = serializers.SerializerMethodField()

    class Meta:
        model = Sport
        fields = ['id', 'name', 'price_per_hour', 'description', 'duration', 'max_players', 'is_active', 
                  'created_at', 'updated_at', 'available_slots_count']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_available_slots_count(self, obj):
        return obj.slots.filter(is_booked=False).count()
    
    def validate_price_per_hour(self, value):
        """Ensure price_per_hour is a valid decimal"""
        if value is None or value == '':
            raise serializers.ValidationError("Price per hour is required")
        try:
            # Convert to Decimal if it's a string
            from decimal import Decimal
            if isinstance(value, str):
                value = Decimal(value)
            if value < 0:
                raise serializers.ValidationError("Price must be 0 or greater")
            return value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid price format")


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot model"""
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    sport_details = SportSerializer(source='sport', read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = ['id', 'sport', 'sport_name', 'sport_details', 'date', 
                  'start_time', 'end_time', 'price', 'is_booked', 'admin_disabled',
                  'max_players', 'is_available', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_available(self, obj):
        """Get computed availability status"""
        return obj.is_available()

    def validate(self, data):
        """Validate that end_time is after start_time"""
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    "End time must be after start time"
                )
        return data


class PlayerSerializer(serializers.ModelSerializer):
    """Serializer for Player model"""
    booking_details = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status', read_only=True)
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['id', 'booking', 'name', 'email', 'phone', 'qr_code', 'qr_token',
                      'qr_code_url', 'check_in_count', 'status', 'last_check_in', 
                      'last_check_out', 'booking_details', 'created_at', 'is_in']
        read_only_fields = ['id', 'qr_code', 'qr_token', 'check_in_count', 'last_check_in', 
                           'last_check_out', 'created_at', 'is_in']

    def get_booking_details(self, obj):
        return {
            'id': obj.booking.id,
            'slot_date': obj.booking.slot.date,
            'sport': obj.booking.slot.sport.name,
            'start_time': obj.booking.slot.start_time,
            'end_time': obj.booking.slot.end_time,
            'organizer': obj.booking.user.email,  # User who made the booking
            'organizer_name': obj.booking.user.get_full_name() or obj.booking.user.email,
        }

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
        return None


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model"""
    user_details = UserSerializer(source='user', read_only=True)
    slot_details = TimeSlotSerializer(source='slot', read_only=True)
    players = PlayerSerializer(many=True, read_only=True)
    player_count = serializers.SerializerMethodField()
    organizer_qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'user', 'user_details', 'slot', 'slot_details', 
                  'players', 'player_count', 'created_at', 'updated_at', 
                  'payment_verified', 'payment_id', 'order_id', 'amount_paid',
                  'is_cancelled', 'cancellation_reason', 'status',
                  'organizer_qr_token', 'organizer_qr_code', 'organizer_qr_code_url',
                  'organizer_is_in', 'organizer_check_in_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'payment_verified', 'status',
                           'organizer_qr_token', 'organizer_qr_code', 'organizer_is_in',
                           'organizer_check_in_count']

    def get_player_count(self, obj):
        return obj.players.count()
    
    def get_organizer_qr_code_url(self, obj):
        """Get full URL for organizer QR code image"""
        if obj.organizer_qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.organizer_qr_code.url)
        return None

    def validate_slot(self, value):
        """Validate that slot is available for booking"""
        if value.is_booked:
            raise serializers.ValidationError("This slot is already booked")
        if not value.is_available():
            raise serializers.ValidationError("This slot is not available")
        return value

    def create(self, validated_data):
        """Create booking and mark slot as booked"""
        booking = super().create(validated_data)
        slot = booking.slot
        slot.is_booked = True
        slot.save()
        return booking


class BookingCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating bookings"""
    class Meta:
        model = Booking
        fields = ['slot']

    def validate_slot(self, value):
        """Validate that slot is available for booking"""
        if value.is_booked:
            raise serializers.ValidationError("This slot is already booked")
        if not value.is_available():
            raise serializers.ValidationError("This slot is not available")
        return value


class PlayerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating players"""
    class Meta:
        model = Player
        fields = ['booking', 'name', 'email', 'phone']

    def validate_email(self, value):
        """Validate email format"""
        return value.lower()


class BulkPlayerCreateSerializer(serializers.Serializer):
    """Serializer for bulk player creation via add_players endpoint"""
    players = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        min_length=1
    )
    
    def validate_players(self, value):
        """Validate each player has required fields"""
        for player_data in value:
            if 'name' not in player_data or not player_data['name'].strip():
                raise serializers.ValidationError("Each player must have a 'name'")
            if 'email' not in player_data or not player_data['email'].strip():
                raise serializers.ValidationError("Each player must have an 'email'")
            
            # Validate email format
            email = player_data['email'].strip().lower()
            try:
                from django.core.validators import validate_email
                validate_email(email)
            except:
                raise serializers.ValidationError(f"Invalid email format: {email}")
            
            player_data['email'] = email  # Normalize email
        
        return value


class CheckInLogSerializer(serializers.ModelSerializer):
    """Serializer for CheckInLog model"""
    player_name = serializers.CharField(source='player.name', read_only=True)
    player_email = serializers.CharField(source='player.email', read_only=True)

    class Meta:
        model = CheckInLog
        fields = ['id', 'player', 'player_name', 'player_email', 'action', 
                  'timestamp', 'location']
        read_only_fields = ['id', 'timestamp']


class QRCodeScanSerializer(serializers.Serializer):
    """Serializer for QR code scanning"""
    qr_data = serializers.JSONField(required=False)
    token = serializers.CharField(required=False)

    def validate_qr_data(self, value):
        """Validate QR code data"""
        required_fields = ['player_id', 'booking_id', 'date']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(
                    f"QR code data must contain '{field}'"
                )
        return value


class PaymentOrderSerializer(serializers.Serializer):
    """Serializer for creating Razorpay order"""
    booking_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for verifying Razorpay payment"""
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
    booking_id = serializers.IntegerField()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value

    def validate_new_password(self, value):
        # add password validators if needed
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

