from django.urls import path
from .views import add_telegram_group

urlpatterns = [
    path('telegram/group/add/', add_telegram_group, name='add_telegram_group')
]