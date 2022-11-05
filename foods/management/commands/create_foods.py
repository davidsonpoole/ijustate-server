from django.core.management import BaseCommand
from foods.models import Food
import os, csv
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        path = str(settings.BASE_DIR) + '/food_data/'
        file_list = os.listdir(path)
        for file in file_list:
            with open(path + file) as f:
                next(f)
                for line in f:
                    arr = line.split(',')
                    f = Food.objects.create(name=arr[0], cal=float(arr[1]), fat=float(arr[2]), car=float(arr[3]), pro=float(arr[4]), serving=arr[5], approved=True)
                    f.save()