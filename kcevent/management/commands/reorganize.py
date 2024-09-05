from django.core.management.base import BaseCommand, CommandError
from kcevent.models import KCEvent
import datetime

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        self.reorganize()
    
    def reorganize(self):
        self.reorganize_events()
    
    def reorganize_events(self):
        # Delete records older than a certain date
        today = datetime.date.today()
        KCEvent.objects.filter(
            deletion_date__isnull=False, deletion_date__lt=today
        ).delete()
