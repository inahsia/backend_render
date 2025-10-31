"""
Set password for superuser
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Old admin credentials
old_email = 'admin@example.com'

# New admin credentials (change these as needed)
new_email = 'aish2716@gmail.com'
new_password = 'admin123'

print("=" * 60)
print("Updating Admin Credentials")
print("=" * 60)

try:
    user = User.objects.get(email=old_email)
    user.email = new_email
    user.set_password(new_password)
    user.save()
    print(f"✓ Admin updated successfully!")
    print(f"  New Email: {new_email}")
    print(f"  New Password: {new_password}")
except User.DoesNotExist:
    print(f"✗ User {old_email} not found. Creating new admin...")
    try:
        user = User.objects.create_superuser(
            email=new_email,
            password=new_password,
            first_name='Admin',
            last_name='User'
        )
        print(f"✓ New admin created successfully!")
        print(f"  Email: {new_email}")
        print(f"  Password: {new_password}")
    except Exception as e:
        print(f"✗ Error: {e}")
