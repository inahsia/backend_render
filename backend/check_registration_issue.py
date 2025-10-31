"""
Check registration issues and provide fixes
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import UserProfile

User = get_user_model()

print('=' * 60)
print('REGISTRATION DIAGNOSTIC TOOL')
print('=' * 60)
print()

# Check 1: Database connectivity
print('1️⃣  Checking database connection...')
try:
    user_count = User.objects.count()
    print(f'   ✅ Database connected - {user_count} users in database')
except Exception as e:
    print(f'   ❌ Database error: {str(e)}')
    exit(1)

print()

# Check 2: Check for existing test email
print('2️⃣  Checking for existing users with common test emails...')
test_emails = [
    'singhaishani2003@gmail.com',
    'test@example.com',
    'player@example.com',
    'admin@example.com'
]

for email in test_emails:
    user = User.objects.filter(email=email).first()
    if user:
        print(f'   ⚠️  Found: {email}')
        print(f'      - ID: {user.id}')
        print(f'      - Name: {user.first_name} {user.last_name}')
        print(f'      - Staff: {user.is_staff}')
        print(f'      - Active: {user.is_active}')
        
        # Check profile
        try:
            profile = user.profile
            print(f'      - Profile Type: {profile.user_type}')
        except:
            print(f'      - Profile: Not created')
    else:
        print(f'   ✅ Available: {email}')

print()

# Check 3: Check Django settings
print('3️⃣  Checking Django settings...')
from django.conf import settings

print(f'   DEBUG: {settings.DEBUG}')
print(f'   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')

# Check CORS settings
if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS'):
    print(f'   CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}')
if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
    print(f'   CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}')

print()

# Check 4: Test registration logic manually
print('4️⃣  Testing registration logic...')
test_email = 'test_new_user@example.com'

# Clean up if exists
existing = User.objects.filter(email=test_email).first()
if existing:
    existing.delete()
    print(f'   🧹 Cleaned up existing test user')

try:
    # Simulate registration
    user = User.objects.create_user(
        email=test_email,
        password='test123',
        first_name='Test',
        last_name='User'
    )
    
    # Check profile creation
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.user_type = 'customer'
    profile.save()
    
    print(f'   ✅ Test registration successful')
    print(f'      - User ID: {user.id}')
    print(f'      - Email: {user.email}')
    print(f'      - Profile: {profile.user_type}')
    
    # Clean up
    user.delete()
    print(f'   🧹 Cleaned up test user')
    
except Exception as e:
    print(f'   ❌ Registration test failed: {str(e)}')
    import traceback
    traceback.print_exc()

print()

# Check 5: Provide solutions
print('=' * 60)
print('SOLUTIONS:')
print('=' * 60)
print()
print('📋 To fix registration issues:')
print()
print('1. Delete existing user (if email already exists):')
print('   python manage.py shell')
print('   >>> from django.contrib.auth import get_user_model')
print('   >>> User = get_user_model()')
print('   >>> User.objects.filter(email="singhaishani2003@gmail.com").delete()')
print()
print('2. Start Django server:')
print('   cd C:\\cricket_acadmy\\backend')
print('   .\\venv\\Scripts\\python.exe manage.py runserver 0.0.0.0:8000')
print()
print('3. Update React Native API config to use your local IP:')
print('   - Open: frontend/src/config/api.ts')
print('   - Change DEV_ANDROID_URL to: http://192.168.3.1:8000')
print('   - Restart React Native app')
print()
print('4. Test registration endpoint:')
print('   python test_registration.py')
print()
