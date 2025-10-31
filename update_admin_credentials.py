"""
Update admin credentials
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# New admin credentials
new_email = 'aish2716@gmail.com'
new_password = 'admin123'

print("=" * 60)
print("Updating Admin Credentials")
print("=" * 60)

# First, try to find any existing admin
admins = User.objects.filter(is_superuser=True)

if admins.exists():
    user = admins.first()
    old_email = user.email
    print(f"Found existing admin: {old_email}")
    
    # Check if new email is already taken by another user
    if User.objects.filter(email=new_email).exclude(id=user.id).exists():
        print(f"✗ Email {new_email} is already taken by another user")
    else:
        user.email = new_email
        user.set_password(new_password)
        user.save()
        print(f"✓ Admin updated successfully!")
        print(f"  Email: {new_email}")
        print(f"  Password: {new_password}")
else:
    # Create new admin
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
