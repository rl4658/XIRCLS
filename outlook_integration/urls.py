from django.urls import path
from . import views

urlpatterns = [
    path('', views.outlook_index, name='outlook_index'),
    path('login/', views.outlook_login, name='outlook_login'),
    path('callback/', views.outlook_callback, name='outlook_callback'),
    path('dashboard/', views.outlook_dashboard, name='outlook_dashboard'),
    path('logout/', views.outlook_logout, name='outlook_logout'),
]
