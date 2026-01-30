from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

# dashboard/models.py - CORRECTED VERSION
class Investment(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey('core.Plan', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    daily_profit = models.DecimalField(max_digits=15, decimal_places=2)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2)
    profit_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    capital_returned = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    last_profit_date = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            # Calculate end date
            self.end_date = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
            
            # Calculate profits
            self.daily_profit = (Decimal(str(self.amount)) * self.plan.daily_percentage) / Decimal('100')
            self.total_profit = self.daily_profit * Decimal(str(self.plan.duration_days))
            
            # Check balance
            if self.amount > self.user.active_balance:
                raise ValueError(f"Insufficient active balance. Available: ${self.user.active_balance}, Required: ${self.amount}")
            
            # Move money from active_balance to investment
            self.user.active_balance -= self.amount
            self.user.save()
        
        super().save(*args, **kwargs)
    
    @property
    def days_remaining(self):
        if self.status != 'ACTIVE':
            return 0
        days_left = (self.end_date - timezone.now()).days
        return max(0, days_left)
    
    @property
    def profit_earned(self):
        if self.status != 'ACTIVE':
            return self.profit_paid
        days_active = (timezone.now() - self.start_date).days
        days_active = min(days_active, self.plan.duration_days)
        earned = self.daily_profit * days_active
        return min(earned, self.total_profit)
    
    @property
    def profit_available(self):
        return self.profit_earned - self.profit_paid
    
    @property
    def total_payout(self):
        return self.amount + self.total_profit
    
    def complete_investment(self):
        if self.status == 'ACTIVE':
            self.status = 'COMPLETED'
            
            # Calculate any remaining profit
            remaining_profit = self.total_profit - self.profit_paid
            if remaining_profit > 0:
                self.user.account_balance += remaining_profit
                self.user.total_earnings += remaining_profit
                self.profit_paid = self.total_profit
            
            # Return capital to account_balance
            self.user.account_balance += self.amount
            self.user.active_balance -= self.amount
            
            # Update investment
            self.capital_returned = True
            self.user.save()
            self.save()
            
            return True
        return False
    
    # ========== NEW REAL-TIME METHODS ==========
    def calculate_profit_up_to_now(self):
        """Calculate profit earned up to current moment"""
        if self.status != 'ACTIVE':
            return self.profit_paid
        
        # Calculate seconds elapsed since start
        now = timezone.now()
        seconds_elapsed = (now - self.start_date).total_seconds()
        days_elapsed = seconds_elapsed / (24 * 3600)
        
        # Don't exceed plan duration
        days_elapsed = min(days_elapsed, self.plan.duration_days)
        
        # Calculate profit
        profit_earned = self.daily_profit * Decimal(str(days_elapsed))
        
        # Don't exceed total profit
        profit_earned = min(profit_earned, self.total_profit)
        
        return profit_earned
    
    @property
    def profit_available_real_time(self):
        """Real-time available profit (not yet paid)"""
        profit_earned = self.calculate_profit_up_to_now()
        return profit_earned - self.profit_paid
    
    def update_profit_if_needed(self):
        """Update profit_paid if there's uncollected profit"""
        profit_earned = self.calculate_profit_up_to_now()
        uncollected = profit_earned - self.profit_paid
        
        if uncollected > 0:
            # Add to user's balance
            self.user.account_balance += uncollected
            self.user.total_earnings += uncollected
            self.profit_paid = profit_earned
            self.last_profit_date = timezone.now()
            
            # Create transaction record
            from .models import Transaction
            Transaction.objects.create(
                user=self.user,
                amount=uncollected,
                transaction_type='profit',
                description=f'Profit update - {self.plan.name}',
                status='completed'
            )
            
            self.user.save()
            self.save()
            
            # Check if investment completed
            if self.profit_paid >= self.total_profit:
                self.complete_investment()
            
            return uncollected
        
        return Decimal('0')
    
    def get_progress_percentage(self):
        """Get investment completion percentage"""
        if self.status != 'ACTIVE':
            return 100
        
        now = timezone.now()
        total_duration = (self.end_date - self.start_date).total_seconds()
        elapsed = (now - self.start_date).total_seconds()
        
        if total_duration > 0:
            percentage = (elapsed / total_duration) * 100
            return min(percentage, 100)
        return 0
    
    def add_daily_profit(self):
        """Add daily profit to user's account_balance (Legacy method - keep for compatibility)"""
        if self.status != 'ACTIVE':
            return False
        
        today = timezone.now().date()
        
        # Check if profit already added today
        if not DailyProfit.objects.filter(
            investment=self, 
            date=today
        ).exists():
            
            # Create daily profit record
            DailyProfit.objects.create(
                investment=self,
                amount=self.daily_profit,
                is_paid=True
            )
            
            # Add profit to user's account_balance
            self.user.account_balance += self.daily_profit
            self.user.total_earnings += self.daily_profit
            self.profit_paid += self.daily_profit
            self.last_profit_date = timezone.now()
            
            # Update investment if completed
            if self.profit_paid >= self.total_profit:
                self.complete_investment()
            else:
                self.user.save()
                self.save()
            
            return True
        return False
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - ${self.amount}"


class UserProfitTracker(models.Model):
    """Track user's profit calculation timeline"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profit_tracker')
    first_deposit_date = models.DateTimeField(null=True, blank=True)
    first_investment_date = models.DateTimeField(null=True, blank=True)
    last_profit_calculation = models.DateTimeField(auto_now=True)
    total_profit_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_calculation_count = models.IntegerField(default=0)
    
    def update_first_deposit(self, date):
        """Set first deposit date if not already set"""
        if not self.first_deposit_date or date < self.first_deposit_date:
            self.first_deposit_date = date
            self.save()
    
    def update_first_investment(self, date):
        """Set first investment date if not already set"""
        if not self.first_investment_date or date < self.first_investment_date:
            self.first_investment_date = date
            self.save()
    
    def calculate_total_available_profit(self):
        """Calculate total profit available across all investments"""
        total = Decimal('0')
        for investment in self.user.investments.filter(status='ACTIVE'):
            total += investment.profit_available_real_time
        return total
    
    def __str__(self):
        return f"Profit Tracker - {self.user.username}"


# ADD Transaction model if it doesn't exist
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('profit', 'Profit'),
        ('investment', 'Investment'),
        ('referral', 'Referral Bonus'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ${self.amount}"


class Deposit(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('TRX', 'TRON'),
        ('USDT', 'USDT'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_CHOICES)
    transaction_hash = models.CharField(max_length=200, blank=True)
    wallet_address = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        old_status = None
        
        if not is_new:
            try:
                old_deposit = Deposit.objects.get(pk=self.pk)
                old_status = old_deposit.status
            except Deposit.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        if not is_new and old_status != self.status:
            if self.status == 'APPROVED' and old_status != 'APPROVED':
                self.user.active_balance += self.amount
                self.user.save()
                self.approved_at = timezone.now()
                
                # Send email
                from django.core.mail import send_mail
                send_mail(
                    'Deposit Approved - Minersurb',
                    f'Your deposit of ${self.amount} has been approved.',
                    'noreply@minersurb.com',
                    [self.user.email],
                    fail_silently=True,
                )
                
                super().save(update_fields=['approved_at'])
            
            elif old_status == 'APPROVED' and self.status != 'APPROVED':
                self.user.active_balance -= self.amount
                self.user.save()
                self.approved_at = None
                super().save(update_fields=['approved_at'])
    
    def approve(self):
        self.status = 'APPROVED'
        self.approved_at = timezone.now()
        self.user.active_balance += self.amount
        self.user.save()
        self.save()
        
        from django.core.mail import send_mail
        send_mail(
            'Deposit Approved - Minersurb',
            f'Your deposit of ${self.amount} has been approved.',
            'noreply@minersurb.com',
            [self.user.email],
            fail_silently=True,
        )
    
    def cancel(self):
        self.status = 'CANCELLED'
        self.save()
        
        from django.core.mail import send_mail
        send_mail(
            'Deposit Cancelled - Minersurb',
            f'Your deposit of ${self.amount} has been cancelled.',
            'noreply@minersurb.com',
            [self.user.email],
            fail_silently=True,
        )


class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    crypto_address = models.CharField(max_length=200)
    crypto_type = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def approve(self):
        if self.user.account_balance >= self.amount:
            self.status = 'APPROVED'
            self.approved_at = timezone.now()
            self.user.account_balance -= self.amount
            self.user.save()
            self.save()
            
            from django.core.mail import send_mail
            send_mail(
                'Withdrawal Approved - Minersurb',
                f'Your withdrawal of ${self.amount} has been approved.',
                'noreply@minersurb.com',
                [self.user.email],
                fail_silently=True,
            )
            return True
        return False
    
    def cancel(self):
        self.status = 'CANCELLED'
        self.save()
        
        from django.core.mail import send_mail
        send_mail(
            'Withdrawal Cancelled - Minersurb',
            f'Your withdrawal of ${self.amount} has been cancelled.',
            'noreply@minersurb.com',
            [self.user.email],
            fail_silently=True,
        )


class DailyProfit(models.Model):
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='daily_profits')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['investment', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.investment.user.username} - ${self.amount} - {self.date}"