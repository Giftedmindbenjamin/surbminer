from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    # Add these fields to override the default ones
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',  # Custom related_name
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions_set',  # Custom related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    
    full_name = models.CharField(max_length=200)
    bitcoin_address = models.CharField(max_length=100, blank=True, null=True)
    ethereum_address = models.CharField(max_length=100, blank=True, null=True)
    trx_address = models.CharField(max_length=100, blank=True, null=True)
    usdt_address = models.CharField(max_length=100, blank=True, null=True)
    
    # Account balances
    active_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    referral_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Referral system
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            import uuid
            self.referral_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.username


class Plan(models.Model):
    PLAN_TYPES = [
        ('BASIC', 'Basic Plan'),
        ('STANDARD', 'Standard Plan'), 
        ('ADVANCED', 'Advanced Plan'),
        ('PREMIUM', 'Premium Plan'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_TYPES)
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    daily_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 3.00 for 3%
    duration_days = models.IntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['min_amount']
    
    def __str__(self):
        return f"{self.name} - {self.daily_percentage}% daily for {self.duration_days} days"
    
    @property
    def total_return_percentage(self):
        """Calculate total return percentage (capital + profit)"""
        return 100 + (self.daily_percentage * self.duration_days)
    
    @property
    def max_amount_display(self):
        """Display for unlimited max amount"""
        if self.max_amount:
            return f"${self.max_amount}"
        return "∞ (Unlimited)"
    
    @property
    def display_range(self):
        """Display amount range"""
        if self.max_amount:
            return f"${self.min_amount} - ${self.max_amount}"
        return f"${self.min_amount} - ∞"