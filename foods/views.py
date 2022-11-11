from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django import forms
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse

from .serializers import FoodSerializer
from .models import Food


class FoodForm(forms.Form):
    name = forms.CharField(max_length=200)
    cal = forms.FloatField(required=False)
    fat = forms.FloatField(required=False)
    car = forms.FloatField(required=False)
    pro = forms.FloatField(required=False)
    serving = forms.CharField(max_length=200, required=False)


class FoodsView(viewsets.ModelViewSet):
    serializer_class = FoodSerializer

    def list(self, request, *args, **kwargs):
        print("Incoming request from " + get_client_ip(request))
        time = request.GET.get('time', None)
        if time is None:
            foods = Food.objects.filter(approved=True).order_by('-modified')
        else:
            time = parse_datetime(time)
            foods = Food.objects.filter(approved=True, modified__gt=time).order_by('-modified')

        res = {
            "foods": FoodSerializer(foods, many=True).data,
            "timestamp": timezone.now()
        }
        json = JSONRenderer().render(res)
        return HttpResponse(json, content_type="application/json")


def validate_inputs(name, cal, fat, car, pro, serving):
    # make sure no injected code
    return


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
