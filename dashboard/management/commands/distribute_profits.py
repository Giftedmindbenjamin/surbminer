from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Investment

class Command(BaseCommand):
    help = 'Distribute daily profits for active investments'
    
    def handle(self, *args, **kwargs):
        active_investments = Investment.objects.filter(status='ACTIVE')
        total_profits = 0
        count = 0
        
        for investment in active_investments:
            if investment.add_daily_profit():
                count += 1
                total_profits += investment.daily_profit
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Distributed ${total_profits} profits to {count} investments'
            )
        )