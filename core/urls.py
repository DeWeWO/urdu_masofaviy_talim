from django.urls import path
from .views import main_v

urlpatterns = [
    path('', main_v, name="main")
]