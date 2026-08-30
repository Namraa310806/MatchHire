from django.urls import path
from .views import RegistrationView, LoginView

app_name = 'users'

urlpatterns = [
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
]
