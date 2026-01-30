# minersurb/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# Import cron functions directly from api/cron.py
# Your api/cron.py contains cron_cleanup and cron_test functions
try:
    # This imports from api/cron.py (not api/cron/cleanup.py)
    from api.cron import cron_cleanup, cron_test
    HAS_CRON = True
    print("✅ Successfully imported cron functions from api/cron.py")
except ImportError as e:
    HAS_CRON = False
    print(f"⚠️ Could not import cron functions: {e}")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core app URLs (landing, auth, etc.)
    path('', include('core.urls', namespace='core')),
    
    # Dashboard app URLs
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    
    # Admin app URLs
    path('admin-panel/', include('admin_panel.urls')),
    
    # Health check endpoint (always available)
    path('api/health', lambda request: JsonResponse({
        'status': 'healthy', 
        'service': 'Minersurb',
        'timestamp': '2024-01-30T12:00:00Z'
    }), name='health_check'),
]

# Add cron endpoints if available
if HAS_CRON:
    urlpatterns += [
        # These point to the functions in api/cron.py
        path('api/cron/cleanup', cron_cleanup, name='cron_cleanup'),
        path('api/cron/test', cron_test, name='cron_test'),
    ]
else:
    # Fallback endpoints
    urlpatterns += [
        path('api/cron/cleanup', lambda request: JsonResponse({
            'error': 'Cron endpoint not configured',
            'solution': 'Check api/cron.py exists and has cron_cleanup function',
            'note': 'Make sure api/cron.py is in the correct location',
            'timestamp': '2024-01-30T12:00:00Z'
        }, status=501), name='cron_cleanup_fallback'),
        path('api/cron/test', lambda request: JsonResponse({
            'status': 'test_mode',
            'message': 'Cron system not configured',
            'timestamp': '2024-01-30T12:00:00Z'
        }), name='cron_test_fallback'),
    ]

# Add static and media URLs for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)