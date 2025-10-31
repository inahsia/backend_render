import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')

app = Celery('redball_academy')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# This module should NOT be executed directly. Running it as a script will shadow
# the third-party 'celery' package and cause circular import errors like:
# "ImportError: cannot import name 'Celery' from partially initialized module 'celery' (.../redball_academy/celery.py)"
# Start a worker using the CLI instead:
#   python -m celery -A redball_academy worker -l info
if __name__ == "__main__":
	import sys
	print(
		"This file is not meant to be executed directly.\n"
		"Start Celery with: python -m celery -A redball_academy worker -l info"
	)
	sys.exit(1)
