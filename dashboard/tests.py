from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from decimal import Decimal
from .models import Deposit, Investment, Withdrawal, DailyProfit
from core.models import Plan

User = get_user_model()

class InvestmentFlowTests(TestCase):
    """Test the complete investment flow"""
    
    def setUp(self):
        """Create test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        
        # Create test plan
        self.plan = Plan.objects.create(
            name='TEST PLAN',
            min_amount=Decimal('100.00'),
            max_amount=Decimal('10000.00'),
            daily_percentage=Decimal('3.00'),  # 3% daily
            duration_days=30,
            is_active=True
        )
    
    def test_deposit_approval_flow(self):
        """Test deposit creation and approval"""
        print("\n=== Testing Deposit Approval ===")
        
        # Create deposit
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            crypto_type='BTC',
            wallet_address='test_wallet_address',
            status='PENDING'
        )
        
        # Verify deposit created
        self.assertEqual(deposit.status, 'PENDING')
        self.assertEqual(deposit.amount, Decimal('1000.00'))
        print(f"✅ Deposit created: ${deposit.amount}")
        
        # Approve deposit
        deposit.approve()
        deposit.refresh_from_db()
        self.user.refresh_from_db()
        
        # Verify approval
        self.assertEqual(deposit.status, 'APPROVED')
        self.assertIsNotNone(deposit.approved_at)
        self.assertEqual(self.user.active_balance, Decimal('1000.00'))
        print(f"✅ Deposit approved")
        print(f"✅ User active_balance: ${self.user.active_balance}")
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Deposit Approved', mail.outbox[0].subject)
        print(f"✅ Email notification sent")
    
    def test_investment_creation_flow(self):
        """Test investment creation with auto-balance deduction"""
        print("\n=== Testing Investment Creation ===")
        
        # First add funds via deposit
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            crypto_type='BTC',
            wallet_address='test',
            status='PENDING'
        )
        deposit.approve()
        self.user.refresh_from_db()
        
        print(f"Initial active_balance: ${self.user.active_balance}")
        
        # Create investment
        investment = Investment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('500.00')
        )
        
        self.user.refresh_from_db()
        
        # Verify investment details
        self.assertEqual(investment.amount, Decimal('500.00'))
        self.assertEqual(investment.status, 'ACTIVE')
        self.assertEqual(investment.daily_profit, Decimal('15.00'))  # 3% of 500
        self.assertEqual(investment.total_profit, Decimal('450.00'))  # 15 * 30
        
        # Verify balance deduction
        self.assertEqual(self.user.active_balance, Decimal('500.00'))  # 1000 - 500
        
        print(f"✅ Investment created: ${investment.amount}")
        print(f"✅ Daily profit: ${investment.daily_profit}")
        print(f"✅ Total profit: ${investment.total_profit}")
        print(f"✅ User active_balance after investment: ${self.user.active_balance}")
    
    def test_daily_profit_distribution(self):
        """Test daily profit distribution"""
        print("\n=== Testing Daily Profit Distribution ===")
        
        # Setup: deposit and investment
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            crypto_type='BTC',
            wallet_address='test',
            status='PENDING'
        )
        deposit.approve()
        
        investment = Investment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('500.00')
        )
        
        self.user.refresh_from_db()
        initial_balance = self.user.account_balance
        initial_earnings = self.user.total_earnings
        
        print(f"Initial account_balance: ${initial_balance}")
        print(f"Initial total_earnings: ${initial_earnings}")
        
        # Distribute daily profit
        success = investment.add_daily_profit()
        
        self.user.refresh_from_db()
        investment.refresh_from_db()
        
        # Verify profit distribution
        self.assertTrue(success)
        self.assertEqual(investment.profit_paid, Decimal('15.00'))
        self.assertEqual(self.user.account_balance, initial_balance + Decimal('15.00'))
        self.assertEqual(self.user.total_earnings, initial_earnings + Decimal('15.00'))
        
        print(f"✅ Daily profit distributed: ${investment.daily_profit}")
        print(f"✅ Profit paid so far: ${investment.profit_paid}")
        print(f"✅ User account_balance: ${self.user.account_balance}")
        print(f"✅ User total_earnings: ${self.user.total_earnings}")
        
        # Verify DailyProfit record created
        daily_profit = DailyProfit.objects.get(investment=investment)
        self.assertTrue(daily_profit.is_paid)
        print(f"✅ DailyProfit record created: ${daily_profit.amount}")
    
    def test_insufficient_balance_for_investment(self):
        """Test that investment fails with insufficient balance"""
        print("\n=== Testing Insufficient Balance ===")
        
        # User has no balance
        self.user.active_balance = Decimal('0.00')
        self.user.save()
        
        print(f"User active_balance: ${self.user.active_balance}")
        
        # Try to create investment with insufficient balance
        with self.assertRaises(ValueError) as context:
            Investment.objects.create(
                user=self.user,
                plan=self.plan,
                amount=Decimal('500.00')
            )
        
        error_msg = str(context.exception)
        self.assertIn('Insufficient active balance', error_msg)
        print(f"✅ Correctly raised error: {error_msg}")
    
    def test_investment_completion(self):
        """Test investment completion with capital return"""
        print("\n=== Testing Investment Completion ===")
        
        # Setup
        deposit = Deposit.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            crypto_type='BTC',
            wallet_address='test',
            status='PENDING'
        )
        deposit.approve()
        
        investment = Investment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('500.00')
        )
        
        # Simulate all profits paid
        investment.profit_paid = investment.total_profit
        investment.save()
        
        self.user.refresh_from_db()
        initial_account_balance = self.user.account_balance
        initial_active_balance = self.user.active_balance
        
        print(f"Before completion:")
        print(f"  Account balance: ${initial_account_balance}")
        print(f"  Active balance: ${initial_active_balance}")
        print(f"  Profit paid: ${investment.profit_paid}")
        print(f"  Total profit: ${investment.total_profit}")
        
        # Complete investment
        success = investment.complete_investment()
        
        self.user.refresh_from_db()
        investment.refresh_from_db()
        
        # Verify completion
        self.assertTrue(success)
        self.assertEqual(investment.status, 'COMPLETED')
        self.assertTrue(investment.capital_returned)
        
        # Capital should return to account_balance
        expected_account_balance = initial_account_balance + investment.amount
        expected_active_balance = initial_active_balance - investment.amount
        
        self.assertEqual(self.user.account_balance, expected_account_balance)
        self.assertEqual(self.user.active_balance, expected_active_balance)
        
        print(f"\nAfter completion:")
        print(f"✅ Investment status: {investment.status}")
        print(f"✅ Capital returned: {investment.capital_returned}")
        print(f"✅ Account balance: ${self.user.account_balance}")
        print(f"✅ Active balance: ${self.user.active_balance}")
    
    def test_withdrawal_flow(self):
        """Test withdrawal creation and approval"""
        print("\n=== Testing Withdrawal Flow ===")
        
        # Give user some account balance
        self.user.account_balance = Decimal('500.00')
        self.user.save()
        
        print(f"Initial account_balance: ${self.user.account_balance}")
        
        # Create withdrawal
        withdrawal = Withdrawal.objects.create(
            user=self.user,
            amount=Decimal('200.00'),
            crypto_address='test_address',
            crypto_type='BTC'
        )
        
        self.assertEqual(withdrawal.status, 'PENDING')
        print(f"✅ Withdrawal created: ${withdrawal.amount}")
        
        # Approve withdrawal
        success = withdrawal.approve()
        
        self.user.refresh_from_db()
        withdrawal.refresh_from_db()
        
        # Verify approval
        self.assertTrue(success)
        self.assertEqual(withdrawal.status, 'APPROVED')
        self.assertEqual(self.user.account_balance, Decimal('300.00'))  # 500 - 200
        
        print(f"✅ Withdrawal approved")
        print(f"✅ User account_balance after withdrawal: ${self.user.account_balance}")
        
        # Verify email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Withdrawal Approved', mail.outbox[0].subject)
        print(f"✅ Email notification sent")
    
    def test_insufficient_balance_for_withdrawal(self):
        """Test withdrawal fails with insufficient balance"""
        print("\n=== Testing Insufficient Balance for Withdrawal ===")
        
        # User has low balance
        self.user.account_balance = Decimal('100.00')
        self.user.save()
        
        print(f"User account_balance: ${self.user.account_balance}")
        
        # Try to withdraw more than balance
        withdrawal = Withdrawal.objects.create(
            user=self.user,
            amount=Decimal('200.00'),
            crypto_address='test_address',
            crypto_type='BTC'
        )
        
        success = withdrawal.approve()
        
        # Should fail
        self.assertFalse(success)
        self.assertEqual(withdrawal.status, 'PENDING')  # Still pending
        self.assertEqual(self.user.account_balance, Decimal('100.00'))  # Unchanged
        
        print(f"✅ Correctly rejected withdrawal (insufficient funds)")

def run_all_tests():
    """Run all tests and print summary"""
    print("=" * 60)
    print("MINERSURB INVESTMENT SYSTEM - COMPLETE TEST SUITE")
    print("=" * 60)
    
    # Create test instance
    test_suite = InvestmentFlowTests()
    test_suite.setUp()
    
    # Run each test
    tests = [
        ('Deposit Approval', test_suite.test_deposit_approval_flow),
        ('Investment Creation', test_suite.test_investment_creation_flow),
        ('Daily Profit', test_suite.test_daily_profit_distribution),
        ('Insufficient Balance', test_suite.test_insufficient_balance_for_investment),
        ('Investment Completion', test_suite.test_investment_completion),
        ('Withdrawal Flow', test_suite.test_withdrawal_flow),
        ('Withdrawal Insufficient', test_suite.test_insufficient_balance_for_withdrawal),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in tests:
        print(f"\n{'='*40}")
        print(f"Running: {test_name}")
        print('='*40)
        
        try:
            test_method()
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print('='*60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print(f"⚠️ {failed} test(s) failed. Check the errors above.")

if __name__ == "__main__":
    run_all_tests()