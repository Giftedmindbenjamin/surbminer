# admin_panel/admin.py - CORRECTED VERSION
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from core.models import User, Plan
from dashboard.models import Investment, Deposit, Withdrawal, DailyProfit
from admin_panel.models import AdminLog, AdminNotification, SiteSetting

# === USER ADMIN ===
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'account_balance', 'active_balance', 
                   'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'referral_code')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'email')}),
        ('Wallet Addresses', {'fields': ('bitcoin_address', 'ethereum_address', 
                                        'trx_address', 'usdt_address')}),
        ('Balances', {'fields': ('account_balance', 'active_balance', 
                                'total_earnings', 'referral_earnings')}),
        ('Referral', {'fields': ('referral_code', 'referred_by')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 
                                   'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'password1', 'password2',
                      'is_staff', 'is_superuser', 'is_active'),
        }),
    )
    
    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff']
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} users activated.')
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} users deactivated.')
    
    def make_staff(self, request, queryset):
        queryset.update(is_staff=True)
        self.message_user(request, f'{queryset.count()} users made staff.')
    
    def remove_staff(self, request, queryset):
        queryset.update(is_staff=False)
        self.message_user(request, f'{queryset.count()} users removed from staff.')

# === PLAN ADMIN ===
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_amount', 'max_amount', 'daily_percentage', 'duration_days')
    list_filter = ('name', 'duration_days')
    search_fields = ('name', 'description')
    
    actions = ['duplicate_plans']
    
    def duplicate_plans(self, request, queryset):
        for plan in queryset:
            plan.pk = None  # This creates a new instance
            plan.name = f"{plan.name} (Copy)"
            plan.save()
        self.message_user(request, f'{queryset.count()} plans duplicated.')

# === INVESTMENT ADMIN ===
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'daily_profit', 'total_profit',
                   'status', 'start_date', 'end_date')
    list_filter = ('status', 'plan', 'start_date')
    search_fields = ('user__username', 'user__email', 'plan__name')
    readonly_fields = ('start_date', 'end_date', 'last_profit_date', 'daily_profit', 'total_profit')
    
    actions = ['complete_investments', 'cancel_investments']
    
    def complete_investments(self, request, queryset):
        queryset.update(status='COMPLETED')
        self.message_user(request, f'{queryset.count()} investments marked as completed.')
    
    def cancel_investments(self, request, queryset):
        queryset.update(status='CANCELLED')
        self.message_user(request, f'{queryset.count()} investments cancelled.')

# === DEPOSIT ADMIN ===
@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'crypto_type', 'status', 'created_at', 'approved_at', 'transaction_hash')
    list_filter = ('status', 'crypto_type', 'created_at')
    search_fields = ('user__username', 'transaction_hash', 'wallet_address')
    readonly_fields = ('created_at', 'approved_at')
   
    
    actions = ['approve_selected_deposits', 'cancel_selected_deposits']
    
    def approve_selected_deposits(self, request, queryset):
        approved_count = 0
        for deposit in queryset.filter(status='PENDING'):
            deposit.approve()
            approved_count += 1
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='DEPOSIT_APPROVE',
                description=f'Approved deposit #{deposit.id} of ${deposit.amount}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        self.message_user(request, f'{approved_count} deposits approved successfully.')
    
    def cancel_selected_deposits(self, request, queryset):
        for deposit in queryset.filter(status='PENDING'):
            deposit.cancel()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='DEPOSIT_CANCEL',
                description=f'Cancelled deposit #{deposit.id} of ${deposit.amount}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        self.message_user(request, f'{queryset.count()} deposits cancelled.')

# === WITHDRAWAL ADMIN ===
@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'crypto_type', 'crypto_address', 'status', 'created_at', 'approved_at')
    list_filter = ('status', 'crypto_type', 'created_at')
    search_fields = ('user__username', 'crypto_address')
    readonly_fields = ('created_at', 'approved_at')
    
    
    actions = ['approve_selected_withdrawals', 'cancel_selected_withdrawals']
    
    def approve_selected_withdrawals(self, request, queryset):
        approved_count = 0
        for withdrawal in queryset.filter(status='PENDING'):
            if withdrawal.approve():
                approved_count += 1
                
                # Log the action
                AdminLog.objects.create(
                    admin=request.user,
                    action='WITHDRAWAL_APPROVE',
                    description=f'Approved withdrawal #{withdrawal.id} of ${withdrawal.amount}',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            else:
                self.message_user(request, f'Withdrawal #{withdrawal.id} failed: insufficient balance', level='ERROR')
        
        self.message_user(request, f'{approved_count} withdrawals approved successfully.')
    
    def cancel_selected_withdrawals(self, request, queryset):
        for withdrawal in queryset.filter(status='PENDING'):
            withdrawal.cancel()
            
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='WITHDRAWAL_CANCEL',
                description=f'Cancelled withdrawal #{withdrawal.id} of ${withdrawal.amount}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        
        self.message_user(request, f'{queryset.count()} withdrawals cancelled.')

# === DAILY PROFIT ADMIN ===
@admin.register(DailyProfit)
class DailyProfitAdmin(admin.ModelAdmin):
    list_display = ('investment', 'amount', 'date')
    list_filter = ('date',)
    search_fields = ('investment__user__username',)
    readonly_fields = ('date',)

# === ADMIN LOG ADMIN ===
@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'description', 'created_at', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('admin__username', 'description', 'ip_address')
    readonly_fields = ('created_at', 'admin', 'action', 'description', 'ip_address')
    
    def has_add_permission(self, request):
        return False  # Logs should only be created by system actions
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be editable

# === ADMIN NOTIFICATION ADMIN ===
@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'message', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('message',)
    readonly_fields = ('created_at', 'notification_type', 'message', 'related_id')
    list_editable = ('is_read',)
    
    actions = ['mark_as_read', 'mark_as_unread', 'clear_notifications']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} notifications marked as read.')
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'{queryset.count()} notifications marked as unread.')
    
    def clear_notifications(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} notifications cleared.')

# === SITE SETTING ADMIN ===
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')
    search_fields = ('key', 'description', 'value')

# === CUSTOM ADMIN SITE CONFIGURATION ===
admin.site.site_header = "Minersurb Admin Panel"
admin.site.site_title = "Minersurb Administration"
admin.site.index_title = "Welcome to Minersurb Admin Panel"

# Optionally unregister Group if you don't need it
# admin.site.unregister(Group)