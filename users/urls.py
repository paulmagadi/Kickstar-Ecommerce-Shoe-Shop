from django.urls import path
from . import views

from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetView


urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify-email'),
    path('resend-verification/', views.resend_verification, name='resend-verification'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('account-settings/', views.account_settings, name='account_settings'),
    path('update/', views.update_user, name='update_user'),
    path('update-password/', views.update_password, name='update_password'),
    path('update-billing/', views.update_billing, name='update_billing'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='email-verify'),
    
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
]

