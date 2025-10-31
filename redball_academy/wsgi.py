"""
WSGI config for redball_academy project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')

application = get_wsgi_application()
