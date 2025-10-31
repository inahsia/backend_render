"""
Views for Red Ball Cricket Academy API
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import razorpay
import hmac
import hashlib
import json
from datetime import datetime, timedelta

User = get_user_model()

from .models import Sport, TimeSlot, Booking, Player, CheckInLog, UserProfile, BookingConfiguration, BreakTime, BlackoutDate, CustomUser
from .serializers import (
    SportSerializer, TimeSlotSerializer, BookingSerializer, 
    PlayerSerializer, CheckInLogSerializer, UserSerializer,
    BookingCreateSerializer, PlayerCreateSerializer, BulkPlayerCreateSerializer,
    QRCodeScanSerializer, PaymentOrderSerializer, PaymentVerificationSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    BookingConfigurationSerializer, BreakTimeSerializer, BlackoutDateSerializer
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
# JWT login endpoint
@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_login(request):
    # Allow login with email or username
    identifier = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')
    
    print(f"🔐 Login attempt - Email/Username: {identifier}, Password provided: {bool(password)}")
    
    user = None
    if identifier and password:
        # CustomUser uses email as USERNAME_FIELD, so authenticate with email
        user = authenticate(request, email=identifier, password=password)
        print(f"   First auth attempt (email): {'✅ Success' if user else '❌ Failed'}")
        
        # Fallback: try as username field for backwards compatibility
        if not user:
            try:
                user_obj = User.objects.filter(email__iexact=identifier).first()
                if user_obj:
                    print(f"   Found user by email: {user_obj.email}")
                    if user_obj.check_password(password):
                        user = user_obj
                        print(f"   Password check: ✅ Success")
                    else:
                        print(f"   Password check: ❌ Failed")
                else:
                    print(f"   No user found with email: {identifier}")
            except Exception as e:
                print(f"   Exception during fallback: {e}")
    else:
        print(f"   ❌ Missing credentials - identifier: {identifier}, password: {bool(password)}")
    
    if user:
        refresh = RefreshToken.for_user(user)
        profile = getattr(user, 'profile', None)
        user_type = profile.user_type if profile else 'customer'
        print(f"   ✅ Login successful for {user.email}")
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'user_type': user_type,
            'is_staff': user.is_staff
        })
    
    print(f"   ❌ Login failed - returning 401")
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{request.scheme}://{request.get_host()}/api/reset-password/?uid={uid}&token={token}"
            # send email
            send_mail(
                subject='Password Reset Request - Red Ball Cricket Academy',
                message=f'Hello,\n\nYou requested to reset your password for Red Ball Cricket Academy.\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 24 hours.\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nRed Ball Cricket Academy Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        # always return success to avoid leaking emails
        return Response({'message': 'If an account with that email exists, a reset link has been sent.'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)
        except Exception:
            return Response({'error': 'Invalid token or uid'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password has been reset successfully'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# JWT register endpoint
@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_register(request):
    email = request.data.get('email')
    password = request.data.get('password')
    user_type = request.data.get('user_type', 'customer')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Ensure profile is created (signal should handle this, but double-check)
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.user_type = user_type
        profile.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User registered successfully',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'user_type': user_type,
            'is_staff': user.is_staff
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class SportViewSet(viewsets.ModelViewSet):
    """ViewSet for Sport CRUD operations"""
    queryset = Sport.objects.all()
    serializer_class = SportSerializer
    
    def get_permissions(self):
        """Authenticated users can manage, anyone can view"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Create sport with detailed error logging"""
        print(f"=== SPORT CREATE ===")
        print(f"User: {request.user}")
        print(f"Is Authenticated: {request.user.is_authenticated}")
        print(f"Auth Header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        print(f"Data: {request.data}")
        print(f"===================")
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"Sport CREATE error: {str(e)}")
            raise
    
    def update(self, request, *args, **kwargs):
        """Update sport with detailed error logging"""
        print(f"=== SPORT UPDATE ===")
        print(f"User: {request.user}")
        print(f"Is Authenticated: {request.user.is_authenticated}")
        print(f"Auth Header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        print(f"Data: {request.data}")
        print(f"===================")
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"Sport UPDATE error: {str(e)}")
            raise
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) sport with detailed error logging"""
        print(f"=== SPORT PATCH ===")
        print(f"User: {request.user}")
        print(f"Is Authenticated: {request.user.is_authenticated}")
        print(f"Auth Header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        print(f"Data: {request.data}")
        print(f"===================")
        try:
            return super().partial_update(request, *args, **kwargs)
        except Exception as e:
            print(f"Sport PATCH error: {str(e)}")
            raise

    @action(detail=True, methods=['get'])
    def available_slots(self, request, pk=None):
        """Get available slots for a specific sport"""
        sport = self.get_object()
        today = timezone.now().date()
        slots = sport.slots.filter(
            is_booked=False,
            admin_disabled=False,
            date__gte=today
        ).order_by('date', 'start_time')
        serializer = TimeSlotSerializer(slots, many=True, context={'request': request})
        return Response(serializer.data)


class SlotViewSet(viewsets.ModelViewSet):
    """ViewSet for Slot CRUD operations"""
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    pagination_class = None  # Disable pagination to show all slots in admin interface

    def get_permissions(self):
        """Admin can create/update/delete, others can only view"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_queryset(self):
        """Filter slots based on query parameters"""
        queryset = TimeSlot.objects.all()
        
        # Hide admin-disabled slots from non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(admin_disabled=False)

        # Filter by sport
        sport_id = self.request.query_params.get('sport', None)
        if sport_id:
            queryset = queryset.filter(sport_id=sport_id)

        # Filter by date
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)

        # Filter by availability
        available = self.request.query_params.get('available', None)
        if available and available.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(is_booked=False, admin_disabled=False, date__gte=today)
        
        # Enhanced logging for debugging
        total_slots = TimeSlot.objects.count()
        print(f"🔍 Slots Query Debug:")
        print(f"   Total slots in DB: {total_slots}")
        print(f"   Query params - Sport: {sport_id}, Date: {date}, Available: {available}")
        print(f"   Filtered count: {queryset.count()}")
        
        # Log a few sample slots
        sample_slots = queryset[:5]
        for slot in sample_slots:
            print(f"   📅 Sample slot: {slot.sport.name} | {slot.date} | {slot.start_time}-{slot.end_time} | Booked: {slot.is_booked}")

        return queryset.order_by('date', 'start_time')

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple slots at once based on booking configuration (Admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            from datetime import datetime, timedelta
            from decimal import Decimal
            
            # Get parameters
            sport_id = request.data.get('sport')
            start_date_str = request.data.get('start_date')
            end_date_str = request.data.get('end_date')
            
            # Manual time slots (optional)
            manual_time_slots = request.data.get('time_slots', [])
            
            # Booking config details (optional - for automatic generation)
            opens_at = request.data.get('opens_at')
            closes_at = request.data.get('closes_at')
            slot_duration = request.data.get('slot_duration', 60)  # default 60 minutes
            buffer_time = request.data.get('buffer_time', 0)
            weekend_opens_at = request.data.get('weekend_opens_at')
            weekend_closes_at = request.data.get('weekend_closes_at')
            force_replace = request.data.get('force_replace', False)  # Option to replace existing slots
            
            if not all([sport_id, start_date_str, end_date_str]):
                return Response(
                    {'error': 'sport, start_date, and end_date are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get sport
            try:
                sport = Sport.objects.get(id=sport_id)
                print(f"✅ Found sport: {sport.name} (ID: {sport_id})")
            except Sport.DoesNotExist:
                print(f"❌ Sport not found: {sport_id}")
                return Response(
                    {'error': 'Sport not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Parse dates first
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError as e:
                return Response(
                    {'error': f'Invalid date format: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Debug: Print all parameters
            print(f"📊 Bulk slot parameters:")
            print(f"   Sport: {sport.name} (ID: {sport_id})")
            print(f"   Date range: {start_date_str} to {end_date_str}")
            print(f"   Opens at: {opens_at}")
            print(f"   Closes at: {closes_at}")
            print(f"   Slot duration: {slot_duration}")
            print(f"   Buffer time: {buffer_time}")
            print(f"   Weekend opens: {weekend_opens_at}")
            print(f"   Weekend closes: {weekend_closes_at}")
            print(f"   Manual slots: {len(manual_time_slots)}")
            
            # Check existing slots for this sport and date range
            existing_slots = TimeSlot.objects.filter(
                sport=sport,
                date__range=[start_date, end_date]
            ).order_by('date', 'start_time')
            
            print(f"🔍 Found {existing_slots.count()} existing slots for this sport in date range:")
            for slot in existing_slots:
                print(f"   📅 {slot.date} {slot.start_time}-{slot.end_time} (ID: {slot.id}, Booked: {slot.is_booked})")
            
            # Validate required configuration
            if not opens_at or not closes_at:
                print(f"❌ Missing operating hours: opens_at={opens_at}, closes_at={closes_at}")
                return Response(
                    {'error': 'Operating hours (opens_at and closes_at) are required for automatic slot generation. Please set up booking configuration for this sport first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not slot_duration:
                print(f"❌ Missing slot duration")
                return Response(
                    {'error': 'Slot duration is required for automatic slot generation. Please set up booking configuration for this sport first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize counters and start processing
            created_slots = []
            skipped_count = 0
            current_date = start_date
            
            while current_date <= end_date:
                # Check if it's a blackout date
                if BlackoutDate.objects.filter(sport=sport, date=current_date, is_active=True).exists():
                    current_date += timedelta(days=1)
                    continue
                
                # Determine operating hours for this date
                is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6
                
                if is_weekend and weekend_opens_at and weekend_closes_at:
                    day_opens_at = weekend_opens_at
                    day_closes_at = weekend_closes_at
                elif opens_at and closes_at:
                    day_opens_at = opens_at
                    day_closes_at = closes_at
                else:
                    # Use manual time slots if no config provided
                    if manual_time_slots:
                        for slot_data in manual_time_slots:
                            start_time_str = slot_data.get('start_time')
                            end_time_str = slot_data.get('end_time')
                            
                            if start_time_str and end_time_str:
                                try:
                                    start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
                                except ValueError:
                                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                                
                                try:
                                    end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
                                except ValueError:
                                    end_time = datetime.strptime(end_time_str, '%H:%M').time()
                                
                                # Check if slot already exists
                                if not TimeSlot.objects.filter(
                                    sport=sport,
                                    date=current_date,
                                    start_time=start_time,
                                    end_time=end_time
                                ).exists():
                                    slot = TimeSlot.objects.create(
                                        sport=sport,
                                        date=current_date,
                                        start_time=start_time,
                                        end_time=end_time,
                                        price=sport.price_per_hour,
                                        max_players=sport.max_players
                                    )
                                    created_slots.append(slot)
                    
                    current_date += timedelta(days=1)
                    continue
                
                # Generate slots automatically based on config
                try:
                    # Try parsing with seconds first (HH:MM:SS)
                    start_time = datetime.strptime(day_opens_at, '%H:%M:%S').time()
                except ValueError:
                    # Fallback to parsing without seconds (HH:MM)
                    start_time = datetime.strptime(day_opens_at, '%H:%M').time()
                
                try:
                    end_time = datetime.strptime(day_closes_at, '%H:%M:%S').time()
                except ValueError:
                    end_time = datetime.strptime(day_closes_at, '%H:%M').time()
                
                # Convert to datetime for calculations
                current_slot_start = datetime.combine(current_date, start_time)
                day_end = datetime.combine(current_date, end_time)
                
                while current_slot_start < day_end:
                    # Calculate slot end time
                    current_slot_end = current_slot_start + timedelta(minutes=slot_duration)
                    
                    # Don't create slot if it goes beyond closing time
                    if current_slot_end.time() > end_time:
                        break
                    
                    # Check if slot already exists
                    existing_slot = TimeSlot.objects.filter(
                        sport=sport,
                        date=current_date,
                        start_time=current_slot_start.time()
                    ).first()
                    
                    if existing_slot:
                        if force_replace:
                            print(f"   🔄 Replacing existing slot: {current_slot_start.time()}-{current_slot_end.time()} (ID: {existing_slot.id})")
                            existing_slot.delete()
                            slot = TimeSlot.objects.create(
                                sport=sport,
                                date=current_date,
                                start_time=current_slot_start.time(),
                                end_time=current_slot_end.time(),
                                price=sport.price_per_hour,
                                max_players=sport.max_players
                                # is_booked defaults to False, which makes slot available
                            )
                            created_slots.append(slot)
                            print(f"   ✅ Created replacement slot: {current_slot_start.time()}-{current_slot_end.time()} (ID: {slot.id})")
                        else:
                            print(f"   ⚠️ Slot already exists: {current_slot_start.time()}-{current_slot_end.time()} (ID: {existing_slot.id})")
                            skipped_count += 1
                    else:
                        slot = TimeSlot.objects.create(
                            sport=sport,
                            date=current_date,
                            start_time=current_slot_start.time(),
                            end_time=current_slot_end.time(),
                            price=sport.price_per_hour,
                            max_players=sport.max_players
                            # is_booked defaults to False, which makes slot available
                        )
                        created_slots.append(slot)
                        print(f"   ✅ Created slot: {current_slot_start.time()}-{current_slot_end.time()} (ID: {slot.id})")
                    
                    # Move to next slot (including buffer time)
                    current_slot_start = current_slot_end + timedelta(minutes=buffer_time)
                
                current_date += timedelta(days=1)
            
            # Serialize created slots
            serializer = TimeSlotSerializer(created_slots, many=True)
            
            response_message = f'Successfully created {len(created_slots)} slots'
            if skipped_count > 0:
                response_message += f' (skipped {skipped_count} existing slots)'
            
            return Response({
                'message': response_message,
                'created_count': len(created_slots),
                'skipped_count': skipped_count,
                'slots': serializer.data
            }, status=status.HTTP_201_CREATED)
            
            return Response({
                'message': response_message,
                'created_count': len(created_slots),
                'skipped_count': skipped_count,
                'slots': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            print(f"Error in bulk_create: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"Request data: {request.data}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'])
    def clear_slots(self, request):
        """Clear all slots for a sport in a date range"""
        sport_id = request.data.get('sport')
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        
        if not all([sport_id, start_date_str, end_date_str]):
            return Response(
                {'error': 'sport, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            sport = Sport.objects.get(id=sport_id)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            slots_to_delete = TimeSlot.objects.filter(
                sport=sport,
                date__range=[start_date, end_date]
            )
            
            deleted_count = slots_to_delete.count()
            slots_to_delete.delete()
            
            return Response({
                'message': f'Successfully deleted {deleted_count} slots',
                'deleted_count': deleted_count
            }, status=status.HTTP_200_OK)
            
        except Sport.DoesNotExist:
            return Response(
                {'error': 'Sport not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BookingViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """Confirm payment for a booking and update status"""
        booking = self.get_object()
        booking.payment_verified = True
        booking.save()
        return Response({'message': 'Payment confirmed', 'status': booking.status})
    """ViewSet for Booking operations"""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users see their own bookings, admins see all"""
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get current user's bookings"""
        bookings = self.get_queryset().order_by('-created_at')
        serializer = BookingSerializer(bookings, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a new booking"""
        serializer = BookingCreateSerializer(data=request.data)
        if serializer.is_valid():
            slot = serializer.validated_data['slot']
            
            # Double-check slot availability
            if slot.is_booked:
                return Response(
                    {'error': 'This slot has already been booked. Please select another slot.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                slot=slot,
                amount_paid=slot.price
            )
            
            # Mark slot as booked
            slot.is_booked = True
            slot.save()
            
            # Return full booking details
            response_serializer = BookingSerializer(booking, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        # Check if user owns the booking or is admin
        if booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking is already cancelled
        if booking.is_cancelled:
            return Response(
                {'error': 'Booking is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Cancelled by user')
        booking.cancel_booking(reason)
        
        serializer = BookingSerializer(booking, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def players(self, request, pk=None):
        """Get all players for a booking"""
        booking = self.get_object()
        players = booking.players.all()
        serializer = PlayerSerializer(players, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='add_players')
    def add_players(self, request, pk=None):
        """Add multiple players to a booking
        POST /api/bookings/<id>/add_players/
        Body: {"players": [{"name": "John", "email": "john@example.com"}, ...]}
        """
        booking = self.get_object()
        
        # Verify booking belongs to user
        if booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to add players to this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check payment verification
        if not booking.payment_verified:
            return Response(
                {'error': 'Payment must be verified before adding players'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate input data
        serializer = BulkPlayerCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        players_data = serializer.validated_data['players']
        
        # Check player limits
        max_allowed = booking.slot.max_players or booking.slot.sport.max_players
        current_count = booking.players.count()
        available_slots = max_allowed - current_count
        
        if len(players_data) > available_slots:
            return Response({
                'error': f'Cannot add {len(players_data)} players. Only {available_slots} slots available.',
                'max_allowed': max_allowed,
                'current_players': current_count,
                'available_slots': available_slots
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create players
        created_players = []
        
        with transaction.atomic():
            for player_data in players_data:
                name = player_data['name'].strip()
                email = player_data['email'].strip().lower()
                phone = player_data.get('phone', '').strip()
                
                # Check for duplicate emails in this booking
                if booking.players.filter(email=email).exists():
                    return Response({
                        'error': f'Player with email {email} already exists in this booking'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create or get user with email as username and "redball" as password
                user, user_created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': name,
                    }
                )
                
                if user_created:
                    user.set_password('redball')
                    user.save()
                    print(f"✅ Created new user account: {email} (password: redball)")
                    
                    # Set user profile as player type
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.user_type = 'player'
                    profile.save()
                else:
                    print(f"ℹ️  Using existing user account: {email}")
                
                # Create player (this triggers the signal for QR and email)
                player = Player.objects.create(
                    booking=booking,
                    name=name,
                    email=email,
                    phone=phone,
                    user=user
                )
                print(f"✅ Created player record for {name} ({email})")
                created_players.append(player)
        
        # Return created players
        response_serializer = PlayerSerializer(
            created_players, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'message': f'Successfully added {len(created_players)} players',
            'players': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def scan_organizer_qr(self, request):
        """Scan organizer QR code for check-in/out"""
        from django.core import signing
        from core.models import OrganizerCheckInLog
        import logging
        
        logger = logging.getLogger(__name__)
        
        token = request.data.get('token')
        logger.info(f"[ORGANIZER QR] Received token: {token[:50]}..." if token and len(token) > 50 else f"[ORGANIZER QR] Received token: {token}")

        if not token:
            logger.error("[ORGANIZER QR] No token provided")
            return Response({'error': 'QR token required'}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Try to decode and verify the token signature FIRST
        try:
            logger.info("[ORGANIZER QR] Attempting to decode token...")
            data = signing.loads(token, salt='organizer-qr-token')
            logger.info(f"[ORGANIZER QR] Token decoded successfully: {data}")
        except signing.BadSignature as e:
            logger.error(f"[ORGANIZER QR] Bad signature: {str(e)}")
            return Response({'error': 'Invalid QR token - signature verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[ORGANIZER QR] Unexpected error during signature verification: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 2: Validate booking and all other checks
        booking_id = data.get('booking_id')
        slot_date = data.get('slot_date')
        logger.info(f"[ORGANIZER QR] Booking ID: {booking_id}, Slot Date: {slot_date}")

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            logger.error(f"[ORGANIZER QR] Booking not found: {booking_id}")
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"[ORGANIZER QR] Booking found: {booking.id}, Slot Date: {booking.slot.date}, Check-in Count: {booking.organizer_check_in_count}")

        today = timezone.now().date()
        logger.info(f"[ORGANIZER QR] Today's date: {today}, Booking slot date: {booking.slot.date}, Token slot date: {slot_date}")

        if str(booking.slot.date) != slot_date or booking.slot.date != today:
            logger.error(f"[ORGANIZER QR] Date mismatch - Today: {today}, Booking: {booking.slot.date}, Token: {slot_date}")
            return Response(
                {'error': 'This QR code is only valid on the booking date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.organizer_check_in_count >= 2:
            logger.error(f"[ORGANIZER QR] Max scans reached: {booking.organizer_check_in_count}")
            return Response(
                {'error': 'Organizer QR code already used (max 2 scans)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 3: Only now, after all checks, update state
        if booking.organizer_check_in_count == 0:
            # First scan - Check IN
            booking.organizer_check_in_count = 1
            booking.organizer_is_in = True
            action = 'IN'
            message = f'Organizer checked in for {booking.slot.sport.name}'
            logger.info(f"[ORGANIZER QR] First scan - CHECK IN")
        elif booking.organizer_check_in_count == 1:
            # Second scan - Check OUT
            booking.organizer_check_in_count = 2
            booking.organizer_is_in = False
            action = 'OUT'
            message = f'Organizer checked out from {booking.slot.sport.name}'
            logger.info(f"[ORGANIZER QR] Second scan - CHECK OUT")
        else:
            logger.error(f"[ORGANIZER QR] Invalid state: {booking.organizer_check_in_count}")
            return Response(
                {'error': 'Invalid check-in state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.save()
        logger.info(f"[ORGANIZER QR] Booking saved - Count: {booking.organizer_check_in_count}, Is In: {booking.organizer_is_in}")

        # Create log entry
        OrganizerCheckInLog.objects.create(booking=booking, user=booking.user, action=action)
        logger.info(f"[ORGANIZER QR] Log entry created")

        return Response({
            'message': message,
            'action': action,
            'booking': {
                'id': booking.id,
                'sport': booking.slot.sport.name,
                'user': booking.user.id,
                'user_email': booking.user.email,
                'organizer_is_in': booking.organizer_is_in,
                'organizer_check_in_count': booking.organizer_check_in_count,
                'slot': {
                    'sport': {'name': booking.slot.sport.name}
                }
            }
        })


class PlayerViewSet(viewsets.ModelViewSet):
    """ViewSet for Player operations"""
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter players based on user role
        - Admins: see all players
        - Players: see only their own player record
        - Customers: see players from their own bookings
        """
        user = self.request.user
        if user.is_staff:
            return Player.objects.all()
        # If logged-in user is a player, return their player profile
        profile = getattr(user, 'profile', None)
        if profile and getattr(profile, 'user_type', None) == 'player':
            return Player.objects.filter(user=user)
        # Otherwise, users see players from their bookings
        return Player.objects.filter(booking__user=user)

    def create(self, request, *args, **kwargs):
        """Create a new player and generate account"""
        serializer = PlayerCreateSerializer(data=request.data)
        if serializer.is_valid():
            booking_id = serializer.validated_data['booking'].id
            
            # Verify booking belongs to user
            booking = get_object_or_404(Booking, id=booking_id)
            if booking.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'You do not have permission to add players to this booking'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if payment is verified
            if not booking.payment_verified:
                return Response(
                    {'error': 'Payment must be verified before adding players'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Enforce max players limit for this slot/sport
            current_count = booking.players.count()
            # Prefer slot.max_players; fallback to sport.max_players
            max_allowed = booking.slot.max_players or booking.slot.sport.max_players
            if current_count >= max_allowed:
                return Response(
                    {
                        'error': f'Maximum players reached for this booking. Allowed: {max_allowed}',
                        'current_players': current_count,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create player. Account creation, QR, and email will be handled by a post_save signal.
            player = serializer.save()
            
            response_serializer = PlayerSerializer(player, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        """Get QR code for player"""
        player = self.get_object()
        if player.qr_code:
            return Response({
                'qr_code_url': request.build_absolute_uri(player.qr_code.url),
                'booking_date': player.booking.slot.date,
                'status': player.get_status()
            })
        return Response(
            {'error': 'QR code not generated'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['post'])
    def scan_qr(self, request):
        """Scan QR code for check-in/out with expiry validation"""
        serializer = QRCodeScanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data.get('token')
        qr_data = serializer.validated_data.get('qr_data')
        player_id = None
        token_date = None
        
        if token:
            # Decode signed token with expiry validation
            from django.core import signing
            from dateutil import parser
            try:
                data = signing.loads(token, salt='player-qr-token')
                player_id = data.get('player_id')
                token_date = data.get('date')
                token_exp = data.get('exp')
                
                # Validate token hasn't expired
                if token_exp:
                    exp_time = parser.isoparse(token_exp)
                    if timezone.now() > exp_time:
                        return Response(
                            {'error': 'QR code has expired. Please contact support.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
            except signing.BadSignature:
                return Response({'error': 'Invalid or tampered QR token'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error': f'QR token error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        elif qr_data:
            player_id = qr_data.get('player_id')
            token_date = qr_data.get('date')
        else:
            return Response({'error': 'No QR data or token provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return Response(
                {'error': 'Invalid QR code - player not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if booking date matches today
        today = timezone.now().date()
        booking_date = player.booking.slot.date
        
        if booking_date != today:
            return Response(
                {'error': f'This QR code is only valid on {booking_date}. Today is {today}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate token date matches booking date
        if token_date and str(booking_date) != token_date:
            return Response(
                {'error': 'QR code date mismatch. This may be an old or invalid code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check in/out
        if player.check_in_count == 0:
            # First scan - Check In
            player.check_in()
            CheckInLog.objects.create(player=player, action='IN')
            message = 'Successfully checked in'
        elif player.check_in_count == 1:
            # Second scan - Check Out
            player.check_in()
            CheckInLog.objects.create(player=player, action='OUT')
            message = 'Successfully checked out'
        else:
            return Response(
                {'error': 'Maximum check-ins reached for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'player': PlayerSerializer(player, context={'request': request}).data
        })

    @action(detail=False, methods=['post'])
    def register_form(self, request):
        """Bulk register players for a booking.
        Payload: {"booking": <id>, "players": [{"name": ..., "email": ..., "phone": ...}, ...]}
        """
        booking_id = request.data.get('booking')
        players = request.data.get('players', [])

        if not booking_id or not isinstance(players, list) or len(players) == 0:
            return Response({'error': 'booking and players[] are required'}, status=status.HTTP_400_BAD_REQUEST)

        booking = get_object_or_404(Booking, id=booking_id)
        # Only owner or admin can add
        if booking.user != request.user and not request.user.is_staff:
            return Response({'error': 'You do not have permission to add players to this booking'}, status=status.HTTP_403_FORBIDDEN)

        if not booking.payment_verified:
            return Response({'error': 'Payment must be verified before adding players'}, status=status.HTTP_400_BAD_REQUEST)

        max_allowed = booking.slot.max_players or booking.slot.sport.max_players
        current_count = booking.players.count()
        available = max_allowed - current_count
        if len(players) > available:
            return Response({'error': f'You can only add {available} more players', 'max_allowed': max_allowed, 'current': current_count}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []
        with transaction.atomic():
            for p in players:
                name = (p or {}).get('name')
                email = (p or {}).get('email')
                phone = (p or {}).get('phone')
                if not name or not email:
                    errors.append({'name': name, 'email': email, 'error': 'name and email are required'})
                    continue
                player = Player.objects.create(booking=booking, name=name, email=email.lower().strip(), phone=phone)
                created.append(player)

        data = PlayerSerializer(created, many=True, context={'request': request}).data
        return Response({'created': len(created), 'players': data, 'errors': errors}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle check-in/check-out for a specific player id (admin/coach tool)"""
        player = self.get_object()
        today = timezone.now().date()
        if str(player.booking.slot.date) != str(today):
            return Response({'error': 'Can only toggle on the booking date'}, status=status.HTTP_400_BAD_REQUEST)
        # Use same logic as scanning
        if player.check_in_count == 0:
            player.check_in()
            CheckInLog.objects.create(player=player, action='IN')
            message = 'Successfully checked in'
        elif player.check_in_count == 1:
            player.check_in()
            CheckInLog.objects.create(player=player, action='OUT')
            message = 'Successfully checked out'
        else:
            return Response({'error': 'Maximum check-ins reached for today'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': message, 'status': player.get_status()})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Return the current player's own records with booking and QR details"""
        user = request.user
        players = Player.objects.filter(user=user).select_related('booking__slot__sport')
        if not players.exists():
            return Response({'error': 'No player profiles found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Return all player records (multiple bookings)
        serializer = PlayerSerializer(players, many=True, context={'request': request})
        return Response(serializer.data)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics (Admin only)"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    today = timezone.now().date()
    
    logs = CheckInLog.objects.select_related('player').order_by('-timestamp')[:20]
    log_data = [
        {
            'player': log.player.name,
            'action': log.action,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'booking_id': log.player.booking.id if log.player.booking else None,
        }
        for log in logs
    ]
    stats = {
        'total_bookings': Booking.objects.filter(payment_verified=True, is_cancelled=False).count(),
        'active_bookings': Booking.objects.filter(payment_verified=True, is_cancelled=False, slot__date__gte=today).count(),
        'total_revenue': sum([
            float(b.amount_paid) for b in Booking.objects.filter(payment_verified=True, is_cancelled=False) if b.amount_paid
        ]),
        'total_players': Player.objects.filter(booking__payment_verified=True, booking__is_cancelled=False).count(),
        'checked_in_today': Player.objects.filter(last_check_in__date=today, booking__payment_verified=True, booking__is_cancelled=False).count(),
        'available_slots': TimeSlot.objects.filter(is_booked=False, admin_disabled=False, date__gte=today).count(),
        'sports_count': Sport.objects.filter(is_active=True).count(),
        'slots_count': TimeSlot.objects.filter(date__gte=today).count(),
        'recent_logs': log_data,
    }
    
    return Response(stats)


class UserViewSet(viewsets.ViewSet):
    """ViewSet for User QR code and check-in operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's info including QR code"""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def scan_qr(self, request):
        """Scan user QR code for check-in/out"""
        from django.core import signing
        from .models import UserCheckInLog
        
        token = request.data.get('token')
        if not token:
            return Response({'error': 'QR token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decode token
            data = signing.loads(token, salt='user-qr-token')
            user_id = data.get('user_id')
            
            # Get user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # Toggle check-in status
            if user.check_in_count == 0 or user.check_in_count == 2:
                # Check in
                user.check_in_count = 1
                user.is_in = True
                action = 'IN'
                message = f'{user.email} checked in successfully'
            elif user.check_in_count == 1:
                # Check out
                user.check_in_count = 2
                user.is_in = False
                action = 'OUT'
                message = f'{user.email} checked out successfully'
            else:
                return Response(
                    {'error': 'Invalid check-in state'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.save()
            
            # Create log entry
            UserCheckInLog.objects.create(user=user, action=action)
            
            return Response({
                'message': message,
                'action': action,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'is_in': user.is_in,
                    'check_in_count': user.check_in_count
                }
            })
            
        except signing.BadSignature:
            return Response({'error': 'Invalid QR token'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookingConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for BookingConfiguration"""
    queryset = BookingConfiguration.objects.all().order_by('id')
    serializer_class = BookingConfigurationSerializer
    
    def get_permissions(self):
        """Authenticated users can manage, anyone can view"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Create booking config with detailed error logging"""
        print(f"=== BOOKING CONFIG CREATE ===")
        print(f"User: {request.user}")
        print(f"Is Authenticated: {request.user.is_authenticated}")
        print(f"Auth Header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        print(f"Data: {request.data}")
        print(f"============================")
        try:
            sport_id = request.data.get('sport')
            
            # Check if config already exists for this sport
            if sport_id:
                existing = BookingConfiguration.objects.filter(sport_id=sport_id).first()
                if existing:
                    print(f"⚠️ Booking config already exists for sport {sport_id}, returning existing config")
                    serializer = self.get_serializer(existing)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print(f"❌ VALIDATION ERRORS: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"❌ BookingConfig CREATE error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update booking config with detailed error logging"""
        print(f"=== BOOKING CONFIG UPDATE ===")
        print(f"User: {request.user}")
        print(f"Is Authenticated: {request.user.is_authenticated}")
        print(f"Auth Header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        print(f"Data: {request.data}")
        print(f"============================")
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"BookingConfig UPDATE error: {str(e)}")
            raise
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) booking config with detailed error logging"""
        print(f"=== BOOKING CONFIG PATCH ===")
        print(f"User: {request.user}")
        print(f"Is Authenticated: {request.user.is_authenticated}")
        print(f"Auth Header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        print(f"Data: {request.data}")
        print(f"============================")
        try:
            return super().partial_update(request, *args, **kwargs)
        except Exception as e:
            print(f"BookingConfig PATCH error: {str(e)}")
            raise
    
    def get_queryset(self):
        """Filter by sport if provided"""
        queryset = BookingConfiguration.objects.all()
        sport_id = self.request.query_params.get('sport', None)
        if sport_id:
            queryset = queryset.filter(sport_id=sport_id)
        return queryset


class BreakTimeViewSet(viewsets.ModelViewSet):
    """ViewSet for BreakTime"""
    queryset = BreakTime.objects.all()
    serializer_class = BreakTimeSerializer
    
    def get_permissions(self):
        """Authenticated users can manage, anyone can view"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter by sport if provided"""
        queryset = BreakTime.objects.all()
        sport_id = self.request.query_params.get('sport', None)
        if sport_id:
            queryset = queryset.filter(sport_id=sport_id)
        return queryset


class BlackoutDateViewSet(viewsets.ModelViewSet):
    """ViewSet for BlackoutDate - date-based unavailability"""
    queryset = BlackoutDate.objects.all()
    serializer_class = BlackoutDateSerializer
    
    def get_permissions(self):
        """Admin can create/update/delete, anyone can view"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        """Filter by sport and/or date range"""
        queryset = BlackoutDate.objects.all().order_by('date')
        
        # Filter by sport
        sport_id = self.request.query_params.get('sport', None)
        if sport_id:
            queryset = queryset.filter(sport_id=sport_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """Create blackout date with duplicate checking"""
        from django.db import IntegrityError
        
        sport_id = request.data.get('sport')
        date = request.data.get('date')
        
        # Check if blackout date already exists
        existing = BlackoutDate.objects.filter(sport_id=sport_id, date=date).first()
        if existing:
            return Response(
                {
                    'error': f'Blackout date already exists for this sport on {date}',
                    'existing_blackout': {
                        'id': existing.id,
                        'reason': existing.reason,
                        'date': existing.date
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Proceed with normal creation, but catch integrity errors
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            # Handle race condition where duplicate was created between check and insert
            existing = BlackoutDate.objects.filter(sport_id=sport_id, date=date).first()
            return Response(
                {
                    'error': f'Blackout date already exists for this sport on {date}',
                    'existing_blackout': {
                        'id': existing.id if existing else None,
                        'reason': existing.reason if existing else 'Unknown',
                        'date': date
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_razorpay_order(request):
    """Create a Razorpay order and return order details"""
    serializer = PaymentOrderSerializer(data=request.data)
    if serializer.is_valid():
        amount = int(float(serializer.validated_data['amount']) * 100)  # Razorpay expects paise
        booking_id = serializer.validated_data['booking_id']
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {'booking_id': str(booking_id)}
        }
        order = client.order.create(data=order_data)
        return Response({
            'order_id': order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'currency': 'INR',
            'booking_id': booking_id
        })
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_razorpay_payment(request):
    """Verify Razorpay payment signature and update booking/payment status"""
    serializer = PaymentVerificationSerializer(data=request.data)
    if serializer.is_valid():
        order_id = serializer.validated_data['razorpay_order_id']
        payment_id = serializer.validated_data['razorpay_payment_id']
        signature = serializer.validated_data['razorpay_signature']
        booking_id = serializer.validated_data['booking_id']
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
        except razorpay.errors.SignatureVerificationError:
            return Response({'error': 'Payment verification failed'}, status=400)
        # Mark booking as paid (update your Booking model as needed)
        from .models import Booking
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.payment_verified = True
            booking.save()
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=404)
        return Response({'message': 'Payment verified and booking updated'})
    return Response(serializer.errors, status=400)

