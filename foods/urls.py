from django.urls import path, include
from . import views
from rest_framework import routers


app_name = 'foods'

router = routers.DefaultRouter()
router.register(r'foods', views.FoodsView, 'foods')

urlpatterns = [
    path('api/foods/', views.getFoods, name='getFoods'),
    path('api/', include(router.urls)),
    path('', views.FoodsHTMLView.as_view(), name='index'),
    path('pending/', views.PendingFoodsView.as_view(), name='pending'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('newFood/', views.new_food, name='newFood'),
]
