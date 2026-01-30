from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import User, Plan
from dashboard.models import Deposit, Withdrawal, Investment, DailyProfit
from admin_panel.models import AdminLog, AdminNotification, SiteSetting

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@staff_member_required
def admin_dashboard(request):
    # Statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    
    # Financial stats
    total_deposits = Deposit.objects.filter(status='APPROVED').aggregate(Sum('amount'))['amount__sum'] or 0
    total_withdrawals = Withdrawal.objects.filter(status='APPROVED').aggregate(Sum('amount'))['amount__sum'] or 0
    total_investments = Investment.objects.filter(status='ACTIVE').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Pending actions
    pending_deposits = Deposit.objects.filter(status='PENDING').count()
    pending_withdrawals = Withdrawal.objects.filter(status='PENDING').count()
    
    # Recent activities
    recent_deposits = Deposit.objects.order_by('-created_at')[:10]
    recent_withdrawals = Withdrawal.objects.order_by('-created_at')[:10]
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Notifications
    unread_notifications = AdminNotification.objects.filter(is_read=False).count()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_investments': total_investments,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'recent_users': recent_users,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@staff_member_required
def user_management(request):
    users = User.objects.all().order_by('-date_joined')
    
    # Filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    context = {
        'users': users,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/user_management.html', context)

@staff_member_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Get user's activities
    deposits = user.deposits.all().order_by('-created_at')
    withdrawals = user.withdrawals.all().order_by('-created_at')
    investments = user.investments.all().order_by('-start_date')
    referrals = user.referrals.all().order_by('-date_joined')
    
    context = {
        'user': user,
        'deposits': deposits,
        'withdrawals': withdrawals,
        'investments': investments,
        'referrals': referrals,
    }
    return render(request, 'admin_panel/user_detail.html', context)

@staff_member_required
def deposit_management(request):
    deposits = Deposit.objects.all().order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', '')
    crypto_filter = request.GET.get('crypto', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status_filter:
        deposits = deposits.filter(status=status_filter)
    
    if crypto_filter:
        deposits = deposits.filter(crypto_type=crypto_filter)
    
    if date_from:
        deposits = deposits.filter(created_at__date__gte=date_from)
    
    if date_to:
        deposits = deposits.filter(created_at__date__lte=date_to)
    
    context = {
        'deposits': deposits,
        'status_filter': status_filter,
        'crypto_filter': crypto_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin_panel/deposit_management.html', context)

@staff_member_required
def approve_deposit(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id)
    
    if request.method == 'POST':
        deposit.approve()
        
        # Log the action
        AdminLog.objects.create(
            admin=request.user,
            action='DEPOSIT_APPROVE',
            description=f'Approved deposit #{deposit.id} of ${deposit.amount} from {deposit.user}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Deposit #{deposit.id} approved successfully.')
        return redirect('admin_panel:deposit_management')
    
    return render(request, 'admin_panel/confirm_approval.html', {
        'object': deposit,
        'type': 'deposit'
    })

@staff_member_required
def cancel_deposit(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id)
    
    if request.method == 'POST':
        deposit.cancel()
        
        # Log the action
        AdminLog.objects.create(
            admin=request.user,
            action='DEPOSIT_CANCEL',
            description=f'Cancelled deposit #{deposit.id} of ${deposit.amount} from {deposit.user}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.warning(request, f'Deposit #{deposit.id} cancelled.')
        return redirect('admin_panel:deposit_management')
    
    return render(request, 'admin_panel/confirm_cancel.html', {
        'object': deposit,
        'type': 'deposit'
    })

@staff_member_required
def withdrawal_management(request):
    withdrawals = Withdrawal.objects.all().order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', '')
    crypto_filter = request.GET.get('crypto', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status_filter:
        withdrawals = withdrawals.filter(status=status_filter)
    
    if crypto_filter:
        withdrawals = withdrawals.filter(crypto_type=crypto_filter)
    
    if date_from:
        withdrawals = withdrawals.filter(created_at__date__gte=date_from)
    
    if date_to:
        withdrawals = withdrawals.filter(created_at__date__lte=date_to)
    
    context = {
        'withdrawals': withdrawals,
        'status_filter': status_filter,
        'crypto_filter': crypto_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin_panel/withdrawal_management.html', context)

@staff_member_required
def approve_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
    
    if request.method == 'POST':
        success = withdrawal.approve()
        
        if success:
            # Log the action
            AdminLog.objects.create(
                admin=request.user,
                action='WITHDRAWAL_APPROVE',
                description=f'Approved withdrawal #{withdrawal.id} of ${withdrawal.amount} from {withdrawal.user}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f'Withdrawal #{withdrawal.id} approved successfully.')
        else:
            messages.error(request, f'Insufficient balance for withdrawal #{withdrawal.id}.')
        
        return redirect('admin_panel:withdrawal_management')
    
    return render(request, 'admin_panel/confirm_approval.html', {
        'object': withdrawal,
        'type': 'withdrawal'
    })

@staff_member_required
def cancel_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
    
    if request.method == 'POST':
        withdrawal.cancel()
        
        # Log the action
        AdminLog.objects.create(
            admin=request.user,
            action='WITHDRAWAL_CANCEL',
            description=f'Cancelled withdrawal #{withdrawal.id} of ${withdrawal.amount} from {withdrawal.user}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.warning(request, f'Withdrawal #{withdrawal.id} cancelled.')
        return redirect('admin_panel:withdrawal_management')
    
    return render(request, 'admin_panel/confirm_cancel.html', {
        'object': withdrawal,
        'type': 'withdrawal'
    })

@staff_member_required
def investment_management(request):
    investments = Investment.objects.all().order_by('-start_date')
    
    # Filters
    status_filter = request.GET.get('status', '')
    plan_filter = request.GET.get('plan', '')
    
    if status_filter:
        investments = investments.filter(status=status_filter)
    
    if plan_filter:
        investments = investments.filter(plan__name=plan_filter)
    
    context = {
        'investments': investments,
        'status_filter': status_filter,
        'plan_filter': plan_filter,
    }
    return render(request, 'admin_panel/investment_management.html', context)

@staff_member_required
def transaction_history(request):
    # Combine deposits and withdrawals
    deposits = Deposit.objects.filter(status='APPROVED').order_by('-approved_at')
    withdrawals = Withdrawal.objects.filter(status='APPROVED').order_by('-approved_at')
    
    # Date filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        deposits = deposits.filter(approved_at__date__gte=date_from)
        withdrawals = withdrawals.filter(approved_at__date__gte=date_from)
    
    if date_to:
        deposits = deposits.filter(approved_at__date__lte=date_to)
        withdrawals = withdrawals.filter(approved_at__date__lte=date_to)
    
    context = {
        'deposits': deposits,
        'withdrawals': withdrawals,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin_panel/transaction_history.html', context)

@staff_member_required
def reports(request):
    today = timezone.now().date()
    
    # Daily stats for the last 30 days
    dates = []
    deposit_data = []
    withdrawal_data = []
    user_data = []
    
    for i in range(30, -1, -1):
        date = today - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
        
        # Deposits for this day
        daily_deposits = Deposit.objects.filter(
            approved_at__date=date,
            status='APPROVED'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        deposit_data.append(float(daily_deposits))
        
        # Withdrawals for this day
        daily_withdrawals = Withdrawal.objects.filter(
            approved_at__date=date,
            status='APPROVED'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        withdrawal_data.append(float(daily_withdrawals))
        
        # New users for this day
        daily_users = User.objects.filter(date_joined__date=date).count()
        user_data.append(daily_users)
    
    context = {
        'dates': dates,
        'deposit_data': deposit_data,
        'withdrawal_data': withdrawal_data,
        'user_data': user_data,
    }
    return render(request, 'admin_panel/reports.html', context)

@admin_required
def admin_logs(request):
    logs = AdminLog.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/admin_logs.html', {'logs': logs})

@staff_member_required
def notifications(request):
    notifications = AdminNotification.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        # Mark all as read
        AdminNotification.objects.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('admin_panel:notifications')
    
    return render(request, 'admin_panel/notifications.html', {'notifications': notifications})

@admin_required
def site_settings(request):
    settings = SiteSetting.objects.all()
    
    if request.method == 'POST':
        for setting in settings:
            value = request.POST.get(setting.key, '')
            if value != setting.value:
                setting.value = value
                setting.save()
        
        messages.success(request, 'Settings updated successfully.')
        return redirect('admin_panel:site_settings')
    
    return render(request, 'admin_panel/site_settings.html', {'settings': settings})