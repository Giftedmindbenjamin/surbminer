# api/index.py
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minersurb.settings')

# Initialize Django
import django
django.setup()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel serverless handler
def handler(request, response):
    """Handle requests in Vercel serverless environment"""
    # Import here to avoid circular imports
    from django.core.handlers.wsgi import WSGIHandler
    from django.http import HttpRequest
    import json
    
    # Create Django request
    django_request = HttpRequest()
    django_request.method = request.method
    django_request.path = request.path
    
    # Convert headers
    for key, value in request.headers.items():
        django_key = f'HTTP_{key.upper().replace("-", "_")}'
        django_request.META[django_key] = value
    
    # Handle request body
    if hasattr(request, 'body') and request.body:
        django_request._body = request.body
        if 'content-type' in request.headers and 'application/json' in request.headers['content-type']:
            try:
                django_request.POST = json.loads(request.body)
            except:
                pass
    
    # Process request
    wsgi_handler = WSGIHandler()
    django_response = wsgi_handler(django_request)
    
    # Set response
    response.status = django_response.status_code
    for header, value in django_response.items():
        response.set_header(header, value)
    
    response.send(django_response.content)
    return response