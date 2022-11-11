from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import generic
from django import forms
from django.views.decorators.csrf import csrf_exempt
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


def getFoods(request):
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


class FoodsHTMLView(generic.ListView):
    template_name = 'foods/index.html'
    context_object_name = 'food_list'

    def get_queryset(self):
        return Food.objects.filter(approved=True)


class PendingFoodsView(generic.ListView):
    template_name = 'foods/index.html'
    context_object_name = 'food_list'

    def get_queryset(self):
        return Food.objects.filter(approved=False)


class DetailView(generic.DetailView):
    model = Food
    template_name = 'foods/detail.html'


@csrf_exempt
def new_food(request):
    if request.method == 'POST':
        name = request.POST['name'] if request.POST['name'] != '' else ''
        cal = request.POST['cal'] if request.POST['cal'] != '' else 0
        fat = request.POST['fat'] if request.POST['fat'] != '' else 0
        car = request.POST['car'] if request.POST['car'] != '' else 0
        pro = request.POST['pro'] if request.POST['pro'] != '' else 0
        serving = request.POST['serving']

        validate_inputs(name, cal, fat, car, pro, serving)
        f = Food.objects.create(name=name, cal=cal, fat=fat, car=car, pro=pro, serving=serving)
        f.save()
        return redirect('/foods')
    return render(request, 'foods/newFood.html')


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
