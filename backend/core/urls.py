"""
URL Configuration for Core app
"""
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sports', views.SportViewSet, basename='sport')
router.register(r'slots', views.SlotViewSet, basename='timeslot')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'players', views.PlayerViewSet, basename='player')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'booking-configurations', views.BookingConfigurationViewSet, basename='booking-configuration')
router.register(r'break-times', views.BreakTimeViewSet, basename='break-time')
router.register(r'blackout-dates', views.BlackoutDateViewSet, basename='blackout-date')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Password Reset Page (for email links)
    path('reset-password/', TemplateView.as_view(template_name='reset_password.html'), name='reset_password_page'),
    
    # Authentication endpoints
    path('auth/jwt_login/', views.jwt_login, name='jwt_login'),
    path('auth/jwt_register/', views.jwt_register, name='jwt_register'),
    path('auth/change-password/', views.change_password, name='change_password'),
    path('auth/password-reset/', views.password_reset_request, name='password_reset_request'),
    path('auth/password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Payment endpoints
    path('payment/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('payment/verify/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
