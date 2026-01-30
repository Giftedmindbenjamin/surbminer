# check_vercel.py
import os
import sys

print('=' * 60)
print('✅ VERCEl DEPLOYMENT CHECK')
print('=' * 60)

# Check critical files
required_files = [
    ('requirements.txt', 'Python dependencies'),
    ('vercel.json', 'Vercel configuration'),
    ('api/index.py', 'Vercel serverless function'),
    ('.vercelignore', 'Ignore file for Vercel'),
]

print('\n📁 FILE CHECK:')
for file, description in required_files:
    exists = os.path.exists(file)
    status = '✅' if exists else '❌'
    print(f'  {status} {file}: {description}')

# Check for Celery (should NOT be in requirements.txt)
print('\n🚫 CELERY CHECK:')
try:
    with open('requirements.txt', 'r') as f:
        content = f.read()
        if 'celery' in content.lower():
            print('  ❌ Celery found in requirements.txt - REMOVE for Vercel!')
        else:
            print('  ✅ No Celery found (good for Vercel)')
except:
    print('  ⚠️ Could not check requirements.txt')

# Check Django settings
print('\n⚙️ DJANGO SETTINGS CHECK:')
settings_path = 'minersurb/settings.py'
if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        content = f.read()
        
        checks = [
            ('DEBUG = False', 'Production debug mode'),
            ('ALLOWED_HOSTS', 'Allowed hosts configured'),
            ('CSRF_TRUSTED_ORIGINS', 'CSRF origins set'),
            ('STATIC_URL', 'Static URL configured'),
            ('whitenoise', 'Whitenoise for static files'),
        ]
        
        for check, description in checks:
            if check in content:
                print(f'  ✅ {description}')
            else:
                print(f'  ⚠️ {description}')
else:
    print('  ❌ Could not find settings.py')

print('\n' + '=' * 60)