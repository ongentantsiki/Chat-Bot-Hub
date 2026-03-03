from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sessions/new/', views.session_create, name='session_create'),
    path('sessions//', views.session_detail, name='session_detail'),
]