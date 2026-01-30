from celery import shared_task
from django.utils import timezone
from dashboard.models import Investment
import logging

logger = logging.getLogger(__name__)

@shared_task
def distribute_profits():
    """
    Task to distribute daily profits to all active investments
    """
    logger.info(f"[{timezone.now()}] Starting profit distribution task")
    
    try:
        active_investments = Investment.objects.filter(status='ACTIVE')
        total_distributed = 0
        count_success = 0
        count_failed = 0
        
        for investment in active_investments:
            try:
                if investment.add_daily_profit():
                    count_success += 1
                    total_distributed += float(investment.daily_profit)
                    logger.info(f"Added profit to Investment {investment.id}: ${investment.daily_profit}")
                else:
                    count_failed += 1
                    logger.warning(f"Failed to add profit to Investment {investment.id}")
            except Exception as e:
                count_failed += 1
                logger.error(f"Error processing Investment {investment.id}: {str(e)}")
                continue
        
        result_message = (
            f"Profit distribution completed: "
            f"Distributed ${total_distributed:.2f} to {count_success} investments. "
            f"Failed: {count_failed}"
        )
        
        logger.info(result_message)
        return result_message
        
    except Exception as e:
        error_message = f"Profit distribution task failed: {str(e)}"
        logger.error(error_message)
        raise