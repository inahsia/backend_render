"""
Update admin email and password
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Change these to your desired credentials
old_email = 'admin@redball.com'
new_email = 'indaish2716@gmail.com'
new_password = 'admin123'  # Change this to your desired password

print("=" * 60)
print("Updating Admin Credentials")
print("=" * 60)

try:
    # Try to find existing admin
    user = User.objects.get(email=old_email)
    user.email = new_email
    user.set_password(new_password)
    user.save()
    print(f"✓ Admin credentials updated successfully!")
    print(f"  New Email: {new_email}")
    print(f"  New Password: {new_password}")
except User.DoesNotExist:
    print(f"✗ User {old_email} not found")
    print(f"\n✓ Creating new admin user...")
    try:
        user = User.objects.create_superuser(
            email=new_email,
            password=new_password,
            first_name='Admin',
            last_name='User'
        )
        print(f"✓ New admin user created successfully!")
        print(f"  Email: {new_email}")
        print(f"  Password: {new_password}")
    except Exception as e:
        print(f"✗ Error creating admin: {e}")

print("=" * 60)
print("\nYou can now login with:")
print(f"  Email: {new_email}")
print(f"  Password: {new_password}")
print("=" * 60)
