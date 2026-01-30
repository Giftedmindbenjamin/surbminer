# check_vercel_ready.py
import os
import sys
import json
import re
from pathlib import Path

print('=' * 70)
print('🚀 VERCEl DEPLOYMENT READINESS CHECK')
print('=' * 70)

def check_file(filepath, description, required=True):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = '✅' if exists else '❌'
    print(f'{status} {description}: {filepath}')
    return exists

def check_requirements():
    """Check requirements.txt for critical packages"""
    print('\n📦 REQUIREMENTS.TXT CHECK:')
    
    if not os.path.exists('requirements.txt'):
        print('❌ requirements.txt not found!')
        return False
    
    with open('requirements.txt', 'r') as f:
        content = f.read().lower()
    
    # Critical packages for Vercel
    critical = [
        ('psycopg2-binary', 'PostgreSQL database'),
        ('whitenoise', 'Static files'),
        ('gunicorn', 'Web server'),
    ]
    
    # Important packages
    important = [
        ('dj-database-url', 'Database URL config'),
        ('cryptography', 'Security'),
    ]
    
    # Problematic packages (should NOT be present)
    problematic = [
        'celery',
        'redis',
        'django-celery-beat',
        'django_celery_results',
    ]
    
    all_ok = True
    
    print('  🔧 Critical packages:')
    for pkg, desc in critical:
        if pkg in content:
            print(f'    ✅ {pkg} - {desc}')
        else:
            print(f'    ❌ {pkg} - {desc} - MISSING!')
            all_ok = False
    
    print('  📋 Important packages:')
    for pkg, desc in important:
        if pkg in content:
            print(f'    ✅ {pkg} - {desc}')
        else:
            print(f'    ⚠️  {pkg} - {desc} - Recommended')
    
    print('  🚫 Problematic packages:')
    found_problematic = []
    for pkg in problematic:
        if pkg in content:
            found_problematic.append(pkg)
    
    if found_problematic:
        print('    ❌ FOUND: ' + ', '.join(found_problematic))
        print('      Remove these for Vercel deployment!')
        all_ok = False
    else:
        print('    ✅ None found (good for Vercel)')
    
    return all_ok

def check_vercel_json():
    """Check vercel.json configuration"""
    print('\n⚡ VERCEl.JSON CHECK:')
    
    if not os.path.exists('vercel.json'):
        print('❌ vercel.json not found!')
        return False
    
    try:
        with open('vercel.json', 'r') as f:
            config = json.load(f)
        
        checks = [
            ('builds', 'Build configuration'),
            ('routes', 'Route configuration'),
            ('PYTHON_VERSION in build.env', 'Python version'),
        ]
        
        all_ok = True
        
        for check, desc in checks:
            if 'builds' in check:
                if 'builds' in config and config['builds']:
                    print(f'    ✅ {desc}')
                else:
                    print(f'    ❌ {desc} - Missing builds config')
                    all_ok = False
            elif 'routes' in check:
                if 'routes' in config and config['routes']:
                    print(f'    ✅ {desc}')
                else:
                    print(f'    ❌ {desc} - Missing routes config')
                    all_ok = False
            elif 'PYTHON_VERSION' in check:
                if ('build' in config and 'env' in config['build'] and 
                    'PYTHON_VERSION' in config['build']['env']):
                    print(f'    ✅ {desc}')
                else:
                    print(f'    ⚠️  {desc} - Not specified (defaults to 3.9)')
        
        # Check for cron configuration
        if 'crons' in config:
            print(f'    ✅ Cron jobs configured: {len(config["crons"])} job(s)')
        else:
            print(f'    ⚠️  Cron jobs not configured (optional)')
        
        return all_ok
        
    except json.JSONDecodeError as e:
        print(f'❌ Invalid JSON in vercel.json: {e}')
        return False
    except Exception as e:
        print(f'❌ Error reading vercel.json: {e}')
        return False

def check_api_structure():
    """Check API structure for Vercel"""
    print('\n📁 API STRUCTURE CHECK:')
    
    checks = [
        ('api/', 'API directory', True),
        ('api/index.py', 'Vercel entry point', True),
        ('api/cron.py', 'Cron endpoint', True),
        ('.vercelignore', 'Vercel ignore file', False),
    ]
    
    all_ok = True
    for path, desc, required in checks:
        exists = os.path.exists(path) if not path.endswith('/') else os.path.isdir(path)
        status = '✅' if exists else ('❌' if required else '⚠️ ')
        print(f'  {status} {desc}: {path}')
        if required and not exists:
            all_ok = False
    
    return all_ok

def check_django_settings():
    """Check Django settings for Vercel compatibility"""
    print('\n⚙️ DJANGO SETTINGS CHECK:')
    
    settings_path = 'minersurb/settings.py'
    if not os.path.exists(settings_path):
        print('❌ settings.py not found!')
        return False
    
    try:
        with open(settings_path, 'r') as f:
            content = f.read()
        
        checks = [
            ('DEBUG = False', 'Production debug mode', False),
            ('ALLOWED_HOSTS', 'Allowed hosts configured', True),
            ('CSRF_TRUSTED_ORIGINS', 'CSRF origins', False),
            ('whitenoise', 'Whitenoise middleware', True),
            ('dj_database_url', 'Database URL config', True),
            ('VERCEL.*os.environ', 'Vercel detection', False),
        ]
        
        all_ok = True
        for check, desc, required in checks:
            if check in content:
                print(f'    ✅ {desc}')
            else:
                status = '❌' if required else '⚠️ '
                print(f'    {status} {desc}')
                if required:
                    all_ok = False
        
        # Check for Celery (should NOT be in production settings)
        if 'CELERY_BROKER_URL' in content and 'redis' in content.lower():
            print('    ⚠️  Celery detected - Disable for Vercel')
        
        return all_ok
        
    except Exception as e:
        print(f'❌ Error reading settings.py: {e}')
        return False

def check_urls():
    """Check URLs configuration"""
    print('\n🔗 URL CONFIGURATION CHECK:')
    
    urls_path = 'minersurb/urls.py'
    if not os.path.exists(urls_path):
        print('❌ urls.py not found!')
        return False
    
    try:
        with open(urls_path, 'r') as f:
            content = f.read()
        
        checks = [
            ('api/cron/cleanup', 'Cron endpoint URL', True),
            ('api/health', 'Health check endpoint', False),
        ]
        
        all_ok = True
        for check, desc, required in checks:
            if check in content:
                print(f'    ✅ {desc}')
            else:
                status = '❌' if required else '⚠️ '
                print(f'    {status} {desc}')
                if required:
                    all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f'❌ Error reading urls.py: {e}')
        return False

def test_django_setup():
    """Test Django setup"""
    print('\n🐘 DJANGO SETUP TEST:')
    
    try:
        # Setup Django
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minersurb.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f'    ✅ Django setup successful')
        print(f'    ✅ DEBUG mode: {settings.DEBUG}')
        print(f'    ✅ Database engine: {settings.DATABASES["default"]["ENGINE"]}')
        
        # Test cron import
        try:
            from api.cron import cron_cleanup, cron_test
            print(f'    ✅ Cron functions imported')
        except ImportError as e:
            print(f'    ❌ Cron import failed: {e}')
            return False
        
        return True
        
    except Exception as e:
        print(f'    ❌ Django setup failed: {e}')
        return False

def main():
    """Run all checks"""
    print('\n📋 RUNNING ALL CHECKS...')
    print('=' * 70)
    
    results = []
    
    # File checks
    print('\n1. 📁 FILE STRUCTURE:')
    results.append(check_file('requirements.txt', 'Requirements file'))
    results.append(check_file('vercel.json', 'Vercel config'))
    results.append(check_file('api/index.py', 'API entry point'))
    results.append(check_file('.vercelignore', 'Ignore file (optional)'))
    
    # Detailed checks
    results.append(check_requirements())
    results.append(check_vercel_json())
    results.append(check_api_structure())
    results.append(check_django_settings())
    results.append(check_urls())
    results.append(test_django_setup())
    
    # Calculate score
    passed = sum([1 for r in results if r])
    total = len(results)
    score = (passed / total) * 100 if total > 0 else 0
    
    print('\n' + '=' * 70)
    print('📊 DEPLOYMENT READINESS SCORE:')
    print('=' * 70)
    print(f'   ✅ Passed: {passed}/{total}')
    print(f'   📈 Score: {score:.1f}%')
    
    if score >= 90:
        print('\n🎉 EXCELLENT! Ready for Vercel deployment!')
        print('\n🚀 DEPLOYMENT COMMANDS:')
        print('   1. vercel login')
        print('   2. vercel')
        print('   3. vercel --prod')
        print('   4. Set environment variables in Vercel dashboard')
    elif score >= 70:
        print('\n⚠️  ALMOST READY! Fix the warnings above.')
    else:
        print('\n❌ NEEDS WORK! Fix critical issues before deploying.')
    
    print('\n🔧 ENVIRONMENT VARIABLES NEEDED ON VERCEl:')
    print('   - SECRET_KEY')
    print('   - DEBUG=False')
    print('   - DATABASE_URL (PostgreSQL)')
    print('   - RESEND_API_KEY (for email)')
    print('   - CRON_SECRET (for cron security)')
    print('   - SITE_URL=https://your-domain.com')
    print('=' * 70)

if __name__ == '__main__':
    main()