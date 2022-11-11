from django.urls import path, include
from . import views
from rest_framework import routers


app_name = 'foods'

router = routers.DefaultRouter()
router.register(r'foods', views.FoodsView, 'foods')

urlpatterns = [
    path('api/', include(router.urls)),
]
