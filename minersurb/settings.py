import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# Vercel-specific detection
IS_VERCEL = "VERCEL" in os.environ

# Debug settings: False on Vercel, True locally
if IS_VERCEL:
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
else:
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS configuration
if IS_VERCEL:
    # On Vercel, use Vercel domains + your domain
    ALLOWED_HOSTS = [
        '.vercel.app',
        '.now.sh',
        'minersurb.com',
        'www.minersurb.com',
        'localhost',
        '127.0.0.1',
    ]
else:
    # Local development
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'core.apps.CoreConfig',
    'dashboard.apps.DashboardConfig',
    'admin_panel.apps.AdminPanelConfig',
    
    # Conditional Celery apps - REMOVE for Vercel
    *(['django_celery_beat', 'django_celery_results'] if not IS_VERCEL else []),
]

TIME_ZONE = 'Europe/Berlin'
USE_TZ = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    # Add whitenoise for Vercel static files
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'minersurb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'minersurb.wsgi.application'

# ==================== DATABASE CONFIGURATION ====================
if IS_VERCEL:
    # Use PostgreSQL on Vercel
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Use SQLite locally
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# ==================== END DATABASE CONFIGURATION ====================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'core.User'

LANGUAGE_CODE = 'en-us'
USE_I18N = True

# ==================== STATIC FILES CONFIGURATION ====================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# ==================== END STATIC FILES ====================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Authentication settings
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ==================== RESEND EMAIL CONFIGURATION ====================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = os.getenv('RESEND_API_KEY', '')
DEFAULT_FROM_EMAIL = 'Minersurb <support@minersurb.com>'
SERVER_EMAIL = 'support@minersurb.com'

# Site URL for password reset links
if IS_VERCEL:
    SITE_URL = os.getenv('SITE_URL', 'https://minersurb.com')
else:
    SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')

EMAIL_SUBJECT_PREFIX = '[Minersurb] '
# ==================== END EMAIL CONFIGURATION ====================

# ==================== CELERY CONFIGURATION ====================
# Disable Celery on Vercel (not supported in serverless)
if IS_VERCEL:
    CELERY_BROKER_URL = None
    CELERY_BROKER_TRANSPORT = None
    CELERY_RESULT_BACKEND = None
else:
    # Optional: Keep Celery for local development only
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_ACCEPT_CONTENT = ['application/json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'Europe/Berlin'
# ==================== END CELERY CONFIGURATION ====================

# ==================== SECURITY SETTINGS FOR PRODUCTION ====================
if IS_VERCEL:
    # Security settings for Vercel production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # CSRF trusted origins for Vercel and your domain
    CSRF_TRUSTED_ORIGINS = [
        'https://minersurb.com',
        'https://www.minersurb.com',
        'https://*.vercel.app',
        'https://*.now.sh',
    ]
    
    # For password reset and other links
    if SITE_URL:
        CSRF_TRUSTED_ORIGINS.append(SITE_URL)
    
    # Secure proxy settings for Vercel
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# ==================== END SECURITY SETTINGS ====================

# ==================== LOGGING CONFIGURATION ====================
if IS_VERCEL:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
# ==================== END LOGGING ====================