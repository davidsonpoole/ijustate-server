from django.db import models
from django.utils import timezone


class Food(models.Model):
    changed = False
    created = models.DateTimeField(editable=False, default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)

    name = models.CharField(max_length=200)
    cal = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    car = models.FloatField(default=0)
    pro = models.FloatField(default=0)
    serving = models.CharField(max_length=200, blank=True)
    approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(Food, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
