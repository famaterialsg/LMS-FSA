from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),  
    path('logout/', LogoutView.as_view(next_page='main:home'), name='logout'),
    path('accounts/login/', views.login_view, name='login'),

    path('register/user_info/', views.register_user_info, name='register_user_info'),
    path('register/confirmation_code/', views.register_confirmation_code, name='register_confirmation_code'),
    path('register_email/', views.register_email, name='register_email'),

    path('resend-code-auto/', views.resend_code_auto, name='resend_code_auto'),
    path('accounts/password_reset/', views.password_reset_request, name='password_reset_request'),
    path('accounts/password_reset_code/', views.password_reset_code, name='password_reset_code'),
    path('accounts/password_reset_form/', views.password_reset_form, name='password_reset_form'),
    
    #2FA
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),      
    path('toggle_2fa/<int:pk>/', views.toggle_2fa, name='toggle_2fa'),
    path('confirm_2fa/<str:token>/', views.confirm_2fa, name='confirm_2fa'),
    
    #lock_wed
    path('lock-site/', views.lock_site, name='lock_site'),
    path('unlock-site/', views.unlock_site, name='unlock_site'),
    path('check-username/', views.check_username, name='check_username'),
]
