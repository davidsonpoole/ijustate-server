from django.contrib import admin
from django.utils import timezone

from .models import Food


@admin.action(description='Approve selected foods to global database')
def approve_foods(modeladmin, request, queryset):
    queryset.update(approved=True, modified=timezone.now())


class FoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'cal', 'fat', 'car', 'pro', 'modified', 'approved']
    ordering = ['approved', '-modified', 'name']
    actions = [approve_foods]


admin.site.register(Food, FoodAdmin)
