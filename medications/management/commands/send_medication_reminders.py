from django.core.management.base import BaseCommand
from django.utils import timezone
from medications.services import medication_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send medication reminders and generate daily schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--generate-schedules',
            action='store_true',
            help='Generate schedules for today',
        )
        parser.add_argument(
            '--send-reminders',
            action='store_true',
            help='Send due medication reminders',
        )
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Send overdue medication alerts',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all tasks',
        )

    def handle(self, *args, **options):
        if options['all']:
            options['generate_schedules'] = True
            options['send_reminders'] = True
            options['send_alerts'] = True

        if options['generate_schedules']:
            self.stdout.write('Generating daily schedules...')
            count = medication_service.generate_schedules_for_date()
            self.stdout.write(
                self.style.SUCCESS(f'Generated {count} medication schedules')
            )

        if options['send_reminders']:
            self.stdout.write('Sending medication reminders...')
            count = medication_service.send_due_medication_reminders()
            self.stdout.write(
                self.style.SUCCESS(f'Sent {count} medication reminders')
            )

        if options['send_alerts']:
            self.stdout.write('Sending overdue alerts...')
            count = medication_service.send_overdue_medication_alerts()
            self.stdout.write(
                self.style.SUCCESS(f'Sent {count} overdue alerts')
            )

        if not any([options['generate_schedules'], options['send_reminders'], options['send_alerts']]):
            self.stdout.write(
                self.style.WARNING('No action specified. Use --help to see available options.')
            )