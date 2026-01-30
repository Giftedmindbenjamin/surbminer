from django.db import models
from django.conf import settings
from django.utils import timezone

class AdminLog(models.Model):
    ACTION_CHOICES = [
        ('DEPOSIT_APPROVE', 'Deposit Approved'),
        ('DEPOSIT_CANCEL', 'Deposit Cancelled'),
        ('WITHDRAWAL_APPROVE', 'Withdrawal Approved'),
        ('WITHDRAWAL_CANCEL', 'Withdrawal Cancelled'),
        ('USER_EDIT', 'User Edited'),
        ('PLAN_EDIT', 'Plan Edited'),
        ('INVESTMENT_CANCEL', 'Investment Cancelled'),
    ]
    
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admin} - {self.action} - {self.created_at}"

class AdminNotification(models.Model):
    TYPE_CHOICES = [
        ('DEPOSIT_PENDING', 'New Deposit Pending'),
        ('WITHDRAWAL_PENDING', 'New Withdrawal Pending'),
        ('USER_VERIFICATION', 'User Verification Needed'),
        ('SYSTEM_ALERT', 'System Alert'),
    ]
    
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    message = models.TextField()
    related_id = models.IntegerField(null=True, blank=True)  # ID of related object
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.created_at}"

class SiteSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.key