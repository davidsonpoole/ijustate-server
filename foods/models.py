from django.db import models
from django.utils import timezone


class Food(models.Model):
    name = models.CharField(max_length=200)
    cal = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    car = models.FloatField(default=0)
    pro = models.FloatField(default=0)
    serving = models.CharField(max_length=200, blank=True)

    approved = models.BooleanField(default=False)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
