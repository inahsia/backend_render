# Cricket Academy Backend Startup Script
# This script will:
# 1. Check if user exists
# 2. Start Django server
# 3. Show connection info for React Native

Write-Host "=" -NoNewline
1..60 | ForEach-Object { Write-Host "=" -NoNewline }
Write-Host ""
Write-Host "   CRICKET ACADEMY - BACKEND SERVER STARTUP" -ForegroundColor Green
Write-Host "=" -NoNewline
1..60 | ForEach-Object { Write-Host "=" -NoNewline }
Write-Host "`n"

# Check if venv exists
if (Test-Path ".\venv\Scripts\python.exe") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "   Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n📋 Checking for test user..." -ForegroundColor Cyan
Write-Host ""

# Check for test user
.\venv\Scripts\python.exe -c @"
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
email = 'singhaishani2003@gmail.com'
user = User.objects.filter(email=email).first()
if user:
    print(f'⚠️  User exists: {email}')
    print(f'   ID: {user.id}, Name: {user.first_name} {user.last_name}')
    print(f'   To delete: python delete_test_user.py')
else:
    print(f'✅ Email available: {email}')
"@

Write-Host "`n" + "=" -NoNewline
1..60 | ForEach-Object { Write-Host "=" -NoNewline }
Write-Host ""
Write-Host "   STARTING DJANGO SERVER" -ForegroundColor Green
Write-Host "=" -NoNewline
1..60 | ForEach-Object { Write-Host "=" -NoNewline }
Write-Host "`n"

# Get local IP
$localIP = (Get-NetIPAddress | Where-Object {$_.AddressFamily -eq 'IPv4' -and $_.IPAddress -notlike '127.*'} | Select-Object -First 1).IPAddress

Write-Host "🌐 Server will be accessible at:" -ForegroundColor Cyan
Write-Host "   - localhost: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   - Local network: http://${localIP}:8000" -ForegroundColor White
Write-Host "   - Android Emulator: http://10.0.2.2:8000" -ForegroundColor White
Write-Host ""

Write-Host "📱 React Native API Config:" -ForegroundColor Cyan
Write-Host "   File: frontend/src/config/api.ts" -ForegroundColor White
Write-Host "   DEV_ANDROID_URL = 'http://10.0.2.2:8000'" -ForegroundColor Yellow
Write-Host "   (Or use http://${localIP}:8000 for physical device)" -ForegroundColor Yellow
Write-Host ""

Write-Host "⚠️  Make sure to:" -ForegroundColor Yellow
Write-Host "   1. Keep this terminal open" -ForegroundColor White
Write-Host "   2. React Native Metro bundler is running" -ForegroundColor White
Write-Host "   3. Android emulator or device is connected" -ForegroundColor White
Write-Host ""

Write-Host "🚀 Starting server..." -ForegroundColor Green
Write-Host ""

# Start Django server
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
