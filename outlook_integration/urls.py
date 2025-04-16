# outlook_integration/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.outlook_login, name='outlook_login'),
    path('callback/', views.outlook_callback, name='outlook_callback'),
    path('dashboard/', views.outlook_dashboard, name='outlook_dashboard'),
]
