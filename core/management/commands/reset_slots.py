from django.core.management.base import BaseCommand
from core.models import TimeSlot

class Command(BaseCommand):
    help = 'Reset all booked slots to available'

    def handle(self, *args, **options):
        count = TimeSlot.objects.filter(is_booked=True).update(is_booked=False)
        self.stdout.write(self.style.SUCCESS(f'Successfully reset {count} slots to available'))
