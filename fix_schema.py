"""
Script to manually add missing columns to core_bookingconfiguration table
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.db import connection

def add_missing_columns():
    with connection.cursor() as cursor:
        # Check if is_active column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='core_bookingconfiguration' 
            AND column_name='is_active';
        """)
        
        if not cursor.fetchone():
            print("Adding is_active column...")
            cursor.execute("""
                ALTER TABLE core_bookingconfiguration 
                ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
            """)
            print("✓ is_active column added")
        else:
            print("✓ is_active column already exists")
        
        # Check if created_at column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='core_bookingconfiguration' 
            AND column_name='created_at';
        """)
        
        if not cursor.fetchone():
            print("Adding created_at column...")
            cursor.execute("""
                ALTER TABLE core_bookingconfiguration 
                ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            """)
            print("✓ created_at column added")
        else:
            print("✓ created_at column already exists")
        
        # Check if updated_at column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='core_bookingconfiguration' 
            AND column_name='updated_at';
        """)
        
        if not cursor.fetchone():
            print("Adding updated_at column...")
            cursor.execute("""
                ALTER TABLE core_bookingconfiguration 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            """)
            print("✓ updated_at column added")
        else:
            print("✓ updated_at column already exists")

if __name__ == '__main__':
    print("Checking and adding missing columns to core_bookingconfiguration...")
    add_missing_columns()
    print("\nSchema fix complete!")
