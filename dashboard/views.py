
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone
from core.models import User, Plan
from .models import Investment, Deposit, Withdrawal, DailyProfit, UserProfitTracker
from datetime import date, timedelta

@login_required
def overview(request):
    user = request.user
    
    # ========== REAL-TIME PROFIT CALCULATION ==========
    # Update profits for all active investments
    total_profit_added_now = Decimal('0')
    active_investments = Investment.objects.filter(user=user, status='ACTIVE')
    
    for investment in active_investments:
        # This calls the new update_profit_if_needed() method
        profit_added = investment.update_profit_if_needed()
        total_profit_added_now += profit_added
    
    # Get or create profit tracker
    try:
        profit_tracker = user.profit_tracker
    except UserProfitTracker.DoesNotExist:
        profit_tracker = UserProfitTracker.objects.create(user=user)
    
    # Update tracker stats
    profit_tracker.total_profit_earned = user.total_earnings
    profit_tracker.save()
    
    # Calculate real-time metrics
    real_time_profit = Decimal('0')
    daily_profit_total = Decimal('0')
    
    for investment in active_investments:
        # Use the new real-time properties
        real_time_profit += investment.profit_available_real_time
        daily_profit_total += investment.daily_profit
    # ========== END REAL-TIME PROFIT ==========
    
    # Calculate totals (your existing code)
    total_deposits = Deposit.objects.filter(
        user=user, 
        status='APPROVED'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_withdrawals = Withdrawal.objects.filter(
        user=user, 
        status='APPROVED'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_referrals = User.objects.filter(referred_by=user).count()
    
    pending_withdrawals = Withdrawal.objects.filter(
        user=user, 
        status='PENDING'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate investment totals
    total_invested = Investment.objects.filter(
        user=user
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_profit_earned = user.total_earnings
    
    # Get recent transactions
    from dashboard.models import Transaction
    recent_transactions = Transaction.objects.filter(
        user=user
    ).order_by('-created_at')[:5]
    
    # Get today's profit
    today = timezone.now().date()
    today_profits = DailyProfit.objects.filter(
        investment__user=user,
        date=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'user': user,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_referrals': total_referrals,
        'pending_withdrawals': pending_withdrawals,
        'active_investments': active_investments,
        
        # NEW: Real-time profit metrics
        'real_time_profit': real_time_profit,
        'daily_profit_total': daily_profit_total,
        'total_profit_added_now': total_profit_added_now,
        'profit_tracker': profit_tracker,
        
        # NEW: Additional investment stats
        'total_invested': total_invested,
        'total_profit_earned': total_profit_earned,
        'today_profits': today_profits,
        
        # NEW: Recent activity
        'recent_transactions': recent_transactions,
        
        # NEW: Investment progress
        'total_investments': Investment.objects.filter(user=user).count(),
        'completed_investments': Investment.objects.filter(user=user, status='COMPLETED').count(),
    }
    
    return render(request, 'dashboard/overview.html', context)



# dashboard/views.py - Updated deposit_view
@login_required
def deposit_view(request):
    """Handle deposit creation"""
    
    # Get all active plans
    plans = Plan.objects.filter(is_active=True).order_by('min_amount')
    
    if request.method == 'POST':
        try:
            # Get form data
            amount = Decimal(request.POST.get('amount', '0'))
            crypto_type = request.POST.get('crypto_type', '')
            plan_id = request.POST.get('plan_id', '')
            
            # Validation
            if amount <= 0:
                messages.error(request, 'Please enter a valid amount')
                return redirect('dashboard:deposit')
            
            if not crypto_type:
                messages.error(request, 'Please select a cryptocurrency')
                return redirect('dashboard:deposit')
            
            # Get company wallet
            COMPANY_WALLETS = {
                'BTC': '1FoBdNHEmiPstsyHrYqWMxCJFJWuSuzG4F',
                'ETH': '0xf09a1b161ee1ad45433a4f8ff476ac5b5c2ba17e',
                'TRX': 'TMgY9cXzFv3sFTUMPnuj34CLdjhTNFKUZA',
                'USDT': '0xf09a1b161ee1ad45433a4f8ff476ac5b5c2ba17e'
            }
            
            company_wallet = COMPANY_WALLETS.get(crypto_type)
            
            # Create deposit
            deposit = Deposit.objects.create(
                user=request.user,
                amount=amount,
                crypto_type=crypto_type,
                wallet_address=company_wallet,
                status='PENDING'
            )
            
            # If plan selected, store it with deposit
            if plan_id:
                try:
                    plan = Plan.objects.get(id=plan_id, is_active=True)
                    deposit.selected_plan = plan
                    deposit.create_investment = True
                    deposit.save()
                except Plan.DoesNotExist:
                    pass
            
            # Show success page
            context = {
                'deposit': deposit,
                'company_wallet': company_wallet,
                'plans': plans,
            }
            
            if plan_id:
                context['selected_plan'] = plan
            
            return render(request, 'dashboard/deposit_success.html', context)
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('dashboard:deposit')
    
    context = {'plans': plans}
    return render(request, 'dashboard/deposit.html', context)
@login_required
def withdrawal_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        crypto_type = request.POST.get('crypto_type')
        crypto_address = request.POST.get('crypto_address')
        
        if amount > request.user.account_balance:
            messages.error(request, 'Insufficient balance')
            return redirect('dashboard:withdrawal')
        
        withdrawal = Withdrawal.objects.create(
            user=request.user,
            amount=amount,
            crypto_type=crypto_type,
            crypto_address=crypto_address
        )
        
        messages.success(request, 'Withdrawal request submitted. Please wait for admin approval.')
        return redirect('dashboard:history')
    
    return render(request, 'dashboard/withdrawal.html')

@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.bitcoin_address = request.POST.get('bitcoin_address', '')
        user.ethereum_address = request.POST.get('ethereum_address', '')
        user.trx_address = request.POST.get('trx_address', '')
        user.usdt_address = request.POST.get('usdt_address', '')
        user.full_name = request.POST.get('full_name', '')
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('dashboard:profile')
    
    return render(request, 'dashboard/profile.html')

@login_required
def history_view(request):
    deposits = Deposit.objects.filter(user=request.user).order_by('-created_at')
    withdrawals = Withdrawal.objects.filter(user=request.user).order_by('-created_at')
    investments = Investment.objects.filter(user=request.user).order_by('-start_date')
    
    # Calculate days active for each investment
    from django.utils import timezone  # Add this import if not already at top
    for investment in investments:
        investment.days_active = (timezone.now() - investment.start_date).days
        if investment.days_active > investment.plan.duration_days:
            investment.days_active = investment.plan.duration_days
    
    context = {
        'deposits': deposits,
        'withdrawals': withdrawals,
        'investments': investments,
        'active_investments': investments.filter(status='ACTIVE'),
        'completed_investments': investments.filter(status='COMPLETED'),
    }
    return render(request, 'dashboard/history.html', context)

@login_required
def referrals_view(request):
    referrals = User.objects.filter(referred_by=request.user)
    referral_link = f"{request.build_absolute_uri('/')[:-1]}/signup/?ref={request.user.referral_code}"
    
    return render(request, 'dashboard/referrals.html', {
        'referrals': referrals,
        'referral_link': referral_link
    })

@login_required
def support_view(request):
    if request.method == 'POST':
        # Handle support message
        message = request.POST.get('message')
        # In production, save to database or send email
        messages.success(request, 'Support message sent successfully')
        return redirect('dashboard:support')
    
    return render(request, 'dashboard/support.html')

def get_company_address(crypto_type):
    # In production, get from database or environment variables
    addresses = {
        'BTC': 'bc1qe38e7d027njcwn50wlhggp0x796j8vtef4ymm7',
        'ETH': '0xB06565931973c1DDAD32850A40ADE39EE1D692f1',
        'TRX': 'TMP7jdfVV8V4Czj8YHYm5ySSEDJHC6HgTL',
        'USDT(TRC 20)': 'TMP7jdfVV8V4Czj8YHYm5ySSEDJHC6HgTL'
    }
    return addresses.get(crypto_type, '')


# dashboard/views.py - Add investment_view
@login_required
def investment_view(request):
    """View to create investment from available balance"""
    
    plans = Plan.objects.filter(is_active=True).order_by('min_amount')
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            plan_id = request.POST.get('plan_id', '')
            
            if amount <= 0:
                messages.error(request, 'Please enter a valid amount')
                return redirect('dashboard:investment')
            
            if not plan_id:
                messages.error(request, 'Please select an investment plan')
                return redirect('dashboard:investment')
            
            # Get plan
            plan = Plan.objects.get(id=plan_id, is_active=True)
            
            # Check amount against plan limits
            if amount < plan.min_amount:
                messages.error(request, 
                    f'Minimum amount for {plan.name} is ${plan.min_amount}')
                return redirect('dashboard:investment')
            
            if plan.max_amount and amount > plan.max_amount:
                messages.error(request,
                    f'Maximum amount for {plan.name} is ${plan.max_amount}')
                return redirect('dashboard:investment')
            
            # Check user balance
            if amount > request.user.account_balance:
                messages.error(request, 'Insufficient balance')
                return redirect('dashboard:investment')
            
            # Create investment
            investment = Investment.objects.create(
                user=request.user,
                plan=plan,
                amount=amount,
                status='ACTIVE'
            )
            
            # Deduct from balance
            # request.user.account_balance -= amount
            # request.user.active_balance += amount
            request.user.save()
            
            messages.success(request, 
                f'Investment created successfully! You will earn ${investment.daily_profit} daily for {plan.duration_days} days.')
            
            return redirect('dashboard:investment_history')
            
        except Plan.DoesNotExist:
            messages.error(request, 'Selected plan is not available')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'plans': plans,
        'user_balance': request.user.account_balance,
    }
    return render(request, 'dashboard/investment.html', context)

@login_required
def investment_history(request):
    """View investment history"""
    investments = Investment.objects.filter(user=request.user).order_by('-start_date')
    
    context = {
        'investments': investments,
        'active_investments': investments.filter(status='ACTIVE'),
        'completed_investments': investments.filter(status='COMPLETED'),
    }
    return render(request, 'dashboard/investment_history.html', context)