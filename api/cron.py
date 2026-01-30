# api/cron.py
import os
import sys
import json
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minersurb.settings')

import django
django.setup()

from dashboard.models import Investment, UserProfitTracker
from django.utils import timezone
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# ==================== ORIGINAL HANDLER CLASS ====================

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Daily cleanup of expired investments and profit tracker updates"""
        try:
            results = {
                'timestamp': timezone.now().isoformat(),
                'expired_investments_processed': 0,
                'profit_trackers_updated': 0,
                'errors': []
            }
            
            # 1. Process expired investments
            expired_investments = Investment.objects.filter(
                status='ACTIVE',
                end_date__lt=timezone.now()
            )
            
            for investment in expired_investments:
                try:
                    if investment.complete_investment():
                        results['expired_investments_processed'] += 1
                        logger.info(f"✅ Completed expired investment #{investment.id} for {investment.user.username}")
                except Exception as e:
                    error_msg = f"Investment #{investment.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(f"❌ Error completing investment #{investment.id}: {str(e)}")
            
            # 2. Update profit trackers (sanity check)
            for tracker in UserProfitTracker.objects.all():
                try:
                    # Ensure total_profit_earned matches user's total_earnings
                    if tracker.total_profit_earned != tracker.user.total_earnings:
                        tracker.total_profit_earned = tracker.user.total_earnings
                        tracker.save()
                        results['profit_trackers_updated'] += 1
                except Exception as e:
                    error_msg = f"Tracker user#{tracker.user.id}: {str(e)}"
                    results['errors'].append(error_msg)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'success': True,
                'message': 'Daily cleanup completed successfully',
                'data': results
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {str(e)}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())

# ==================== DJANGO VIEW FUNCTIONS (REQUIRED FOR URLS.PY) ====================

@csrf_exempt
@require_POST
def cron_cleanup(request):
    """Django view for cron cleanup - Vercel will call this"""
    try:
        # Simple implementation using your handler logic
        results = {
            'timestamp': timezone.now().isoformat(),
            'expired_investments_processed': 0,
            'profit_trackers_updated': 0,
        }
        
        # Process expired investments
        expired_investments = Investment.objects.filter(
            status='ACTIVE',
            end_date__lt=timezone.now()
        )
        
        for investment in expired_investments:
            try:
                if hasattr(investment, 'complete_investment'):
                    if investment.complete_investment():
                        results['expired_investments_processed'] += 1
            except Exception as e:
                logger.error(f"Error completing investment #{investment.id}: {e}")
        
        # Update profit trackers
        for tracker in UserProfitTracker.objects.all():
            try:
                user_investments = Investment.objects.filter(user=tracker.user)
                total_earned = sum([inv.total_profit for inv in user_investments])
                
                if tracker.total_profit_earned != total_earned:
                    tracker.total_profit_earned = total_earned
                    tracker.save()
                    results['profit_trackers_updated'] += 1
            except Exception as e:
                logger.error(f"Error updating tracker: {e}")
        
        logger.info(f"Cron cleanup completed: {results}")
        
        return JsonResponse({
            'success': True,
            'message': 'Cron cleanup completed successfully',
            'data': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cron cleanup failed: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)

@csrf_exempt
def cron_test(request):
    """Test endpoint for cron functionality"""
    return JsonResponse({
        'status': 'ok',
        'service': 'Minersurb Cron',
        'endpoints': {
            'cleanup': 'POST /api/cron/cleanup - Runs cleanup tasks',
            'test': 'GET /api/cron/test - This endpoint'
        },
        'timestamp': datetime.now().isoformat()
    })