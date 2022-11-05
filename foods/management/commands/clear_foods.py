from django.core.management import BaseCommand
from foods.models import Food


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = input("Are you sure you want to clear the database? (Y/N) ")
        if response == 'Y':
            Food.objects.all().delete()
            print("Foods cleared")
        else:
            print("Not cleared")