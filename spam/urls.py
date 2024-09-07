from django.urls import path
from . import views

urlpatterns = [
   
    path('', views.list,name='home'),
    path('display/<int:id>/', views.display,name='display'),
    path('list/', views.list,name='list'),
    path('create/', views.create,name='create'),
    path('check/', views.check, name='check'),
    path('spam/',views.spamlist,name='spamlist'),
    path('search/', views.search, name='search'),
]
