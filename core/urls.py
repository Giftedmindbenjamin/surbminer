from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Landing & Main Pages
    path('', views.landing, name='landing'),
    
    # Authentication
    path('auth/login/', views.login_view, name='login'),
    path('auth/signup/', views.signup, name='signup'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Password Reset Flow
    path('auth/password-reset/', views.password_reset_request, name='password_reset'),
    path('auth/password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('auth/password-reset-confirm/<uidb64>/<token>/', 
         views.password_reset_confirm_view, 
         name='password_reset_confirm'),
    path('auth/password-reset/complete/', 
         views.password_reset_complete_view, 
         name='password_reset_complete'),
    
    # AJAX Validation Endpoints
    path('auth/check-username/', views.check_username, name='check_username'),
    path('auth/check-email/', views.check_email, name='check_email'),
    
    # User Profile (Protected)
    path('profile/', views.profile_view, name='profile'),
    
    
]