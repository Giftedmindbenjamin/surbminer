from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.utils import timezone  # ✅ ADDED THIS IMPORT
from .models import User
from .forms import CustomUserCreationForm
import re

def landing(request):
    """Landing page for non-authenticated users"""
    return render(request, 'core/landing.html')

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        confirm_email = request.POST.get('confirm_email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Get crypto addresses (optional)
        bitcoin_address = request.POST.get('bitcoin_address', '')
        ethereum_address = request.POST.get('ethereum_address', '')
        trx_address = request.POST.get('trx_address', '')
        usdt_address = request.POST.get('usdt_address', '')
        
        # Validation
        errors = []
        
        if email != confirm_email:
            errors.append('Emails do not match')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered')
        
        # Email format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            # Preserve form data
            context = {
                'full_name': full_name,
                'username': username,
                'email': email,
                'confirm_email': confirm_email,
                'bitcoin_address': bitcoin_address,
                'ethereum_address': ethereum_address,
                'trx_address': trx_address,
                'usdt_address': usdt_address,
                'referral_code': request.GET.get('ref', '')
            }
            return render(request, 'core/signup.html', context)
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                bitcoin_address=bitcoin_address,
                ethereum_address=ethereum_address,
                trx_address=trx_address,
                usdt_address=usdt_address
            )
            
            # Handle referral if any
            referral_code = request.GET.get('ref')
            if referral_code:
                try:
                    referrer = User.objects.get(referral_code=referral_code)
                    user.referred_by = referrer
                    user.save()
                    messages.success(request, f'You were referred by {referrer.username}')
                except User.DoesNotExist:
                    pass
            
            # Auto login
            login(request, user)
            
            # ========== FIXED WELCOME EMAIL SECTION ==========
            # Send welcome email
            try:
                subject = 'Welcome to Minersurb - Your Investment Journey Begins!'
                message = render_to_string('emails/welcome_email.html', {
                    'user': user,
                    'site_url': settings.SITE_URL,  # ✅ FIXED: Changed from 'site_name'
                    'current_year': timezone.now().year  # ✅ ADDED for template
                })
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,  # ✅ FIXED: Changed from True to see errors
                    html_message=message
                )
                messages.info(request, 'Welcome email sent! Check your inbox.')
            except Exception as e:
                # Log error but don't fail signup
                print(f"Welcome email failed: {e}")
                messages.warning(request, 'Account created, but welcome email could not be sent.')
            # ========== END FIX ==========
            
            messages.success(request, 'Account created successfully! Welcome to Minersurb!')
            return redirect('dashboard:overview')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            # Preserve form data on error
            context = {
                'full_name': full_name,
                'username': username,
                'email': email,
                'confirm_email': confirm_email,
                'bitcoin_address': bitcoin_address,
                'ethereum_address': ethereum_address,
                'trx_address': trx_address,
                'usdt_address': usdt_address,
                'referral_code': request.GET.get('ref', '')
            }
            return render(request, 'core/signup.html', context)
    
    # GET request - show signup form
    referral_code = request.GET.get('ref', '')
    return render(request, 'core/signup.html', {'referral_code': referral_code})

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard:overview')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember') == 'on'
        
        # Try to authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Handle remember me
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            
            messages.success(request, f'Welcome back, {user.full_name or user.username}!')
            
            # Redirect to next page if exists
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)
            return redirect('dashboard:overview')
        else:
            # Check if username/email exists
            try:
                user_by_username = User.objects.get(username=username)
                messages.error(request, 'Incorrect password. Please try again.')
            except User.DoesNotExist:
                try:
                    user_by_email = User.objects.get(email=username)
                    messages.error(request, 'Incorrect password. Please try again.')
                except User.DoesNotExist:
                    messages.error(request, 'Username or email not found. Please check your credentials.')
        
        return render(request, 'core/login.html', {'username': username})
    
    return render(request, 'core/login.html')

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('core:landing')


def password_reset_request(request):
    """Password reset request view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate token and send email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL - FIXED: Use your actual domain
            reset_url = f"{settings.SITE_URL}/auth/password-reset-confirm/{uid}/{token}/"
            
            # Send email
            subject = 'Password Reset Request - Minersurb'
            message = render_to_string('emails/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'site_name': 'Minersurb'
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,  # Change to False to see errors
                html_message=message
            )
            
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('core:password_reset_done')  # ✅ FIXED
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'core/password_reset.html')

def password_reset_done_view(request):
    """Password reset done view"""
    return render(request, 'core/password_reset_done.html')

def password_reset_confirm_view(request, uidb64, token):
    """Password reset confirmation view"""
    try:
        # Decode user ID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validation
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'core/password_reset_confirm.html', {'validlink': True})
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'core/password_reset_confirm.html', {'validlink': True})
            
            # Set new password
            user.set_password(password)
            user.save()
            
            # Auto login
            login(request, user)
            
            messages.success(request, 'Your password has been reset successfully!')
            return redirect('core:password_reset_complete')  
        
        return render(request, 'core/password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return render(request, 'core/password_reset_confirm.html', {'validlink': False})

def password_reset_complete_view(request):
    """Password reset complete view"""
    return render(request, 'core/password_reset_complete.html')

def check_username(request):
    """Check if username is available (AJAX)"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        username = request.GET.get('username', '')
        exists = User.objects.filter(username=username).exists()
        return HttpResponse('taken' if exists else 'available')
    return HttpResponse('error')

def check_email(request):
    """Check if email is available (AJAX)"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        email = request.GET.get('email', '')
        exists = User.objects.filter(email=email).exists()
        return HttpResponse('taken' if exists else 'available')
    return HttpResponse('error')

@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'core/profile.html', {'user': request.user})

# Optional: Create a form for cleaner validation
from django import forms

class CustomUserCreationForm(forms.ModelForm):
    confirm_email = forms.EmailField(label='Confirm Email')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    
    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if email and confirm_email and email != confirm_email:
            raise forms.ValidationError("Emails do not match")
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

class CustomSetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data