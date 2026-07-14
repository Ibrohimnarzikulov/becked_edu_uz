"""Wait for database to become available.

Usage: python manage.py wait_for_db
"""
import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Waits for the database to be ready."

    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        conn = None
        attempts = 0
        max_attempts = 60
        while not conn and attempts < max_attempts:
            try:
                connections["default"].cursor()
                conn = True
            except OperationalError:
                self.stdout.write(
                    self.style.WARNING(
                        f"Database unavailable (attempt {attempts + 1}/{max_attempts}), waiting 1s..."
                    )
                )
                time.sleep(1)
                attempts += 1

        if not conn:
            raise OperationalError("Database did not become available in time.")

        self.stdout.write(self.style.SUCCESS("Database available!"))
