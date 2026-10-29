import csv
import os

from django.conf import settings
from django.core.management import BaseCommand

from foods.models import Food


class Command(BaseCommand):
    help = "Load/refresh the approved food catalog from food_data/*.csv"

    def handle(self, *args, **options):
        path = os.path.join(str(settings.BASE_DIR), 'food_data')
        created = updated = skipped = 0

        for filename in sorted(os.listdir(path)):
            if not filename.endswith('.csv'):
                continue
            with open(os.path.join(path, filename), newline='') as fh:
                reader = csv.reader(fh)
                next(reader, None)  # header
                for row in reader:
                    if len(row) < 5 or not row[0].strip():
                        skipped += 1
                        continue
                    try:
                        values = {
                            'cal': float(row[1]),
                            'fat': float(row[2]),
                            'car': float(row[3]),
                            'pro': float(row[4]),
                            # Was unstripped, so every row stored a bare "\n".
                            'serving': (row[5].strip() if len(row) > 5 else ''),
                            'approved': True,
                        }
                    except ValueError:
                        skipped += 1
                        self.stderr.write(f"  skipped malformed row in {filename}: {row!r}")
                        continue

                    # Keyed on name so re-running refreshes instead of
                    # duplicating. Previously a second run doubled the catalog.
                    _, was_created = Food.objects.update_or_create(
                        name=row[0].strip(), defaults=values
                    )
                    created += was_created
                    updated += not was_created

        self.stdout.write(
            f"created {created}, updated {updated}, skipped {skipped} "
            f"(total approved: {Food.objects.filter(approved=True).count()})"
        )
