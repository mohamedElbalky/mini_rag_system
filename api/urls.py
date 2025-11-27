from django.urls import path
from .views import register, login

urlpatterns = [
    # Authentication
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
]