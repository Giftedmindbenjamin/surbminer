# dashboard/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from core.models import User
from .models import UserProfitTracker, Deposit, Investment, Transaction
from decimal import Decimal

@receiver(post_save, sender=User)
def create_user_profit_tracker(sender, instance, created, **kwargs):
    """Create profit tracker when user is created"""
    if created:
        UserProfitTracker.objects.create(user=instance)

@receiver(post_save, sender=Deposit)
def update_deposit_tracker(sender, instance, created, **kwargs):
    """Update profit tracker when deposit is approved"""
    if instance.status == 'APPROVED':
        try:
            tracker = UserProfitTracker.objects.get(user=instance.user)
            tracker.update_first_deposit(instance.created_at)
            tracker.save()
        except UserProfitTracker.DoesNotExist:
            tracker = UserProfitTracker.objects.create(user=instance.user)
            tracker.update_first_deposit(instance.created_at)

@receiver(post_save, sender=Investment)
def update_investment_tracker(sender, instance, created, **kwargs):
    """Update profit tracker when investment is created"""
    if created:
        try:
            tracker = UserProfitTracker.objects.get(user=instance.user)
            tracker.update_first_investment(timezone.now())
            tracker.save()
        except UserProfitTracker.DoesNotExist:
            tracker = UserProfitTracker.objects.create(user=instance.user)
            tracker.update_first_investment(timezone.now())

@receiver(post_save, sender=Transaction)
def update_profit_earned(sender, instance, created, **kwargs):
    """Update total profit earned in tracker"""
    if created and instance.transaction_type == 'profit' and instance.status == 'completed':
        try:
            tracker = UserProfitTracker.objects.get(user=instance.user)
            tracker.total_profit_earned += instance.amount
            tracker.profit_calculation_count += 1
            tracker.save()
        except UserProfitTracker.DoesNotExist:
            tracker = UserProfitTracker.objects.create(
                user=instance.user,
                total_profit_earned=instance.amount,
                profit_calculation_count=1
            )