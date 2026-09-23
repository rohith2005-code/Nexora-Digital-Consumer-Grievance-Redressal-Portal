"""
WSGI config for grievance_core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grievance_core.settings')

application = get_wsgi_application()

# Guarantee default accounts and migrations on server boot
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    from complaints.views import ensure_default_accounts
    ensure_default_accounts()
except Exception as e:
    print("Auto-seed error on WSGI boot:", e)
