from django.urls import path
from .views import add_telegram_group, RegisterListCreateView, RegisterDetailView

urlpatterns = [
    path('telegram/group/add/', add_telegram_group, name='add_telegram_group'),
    path('register/', RegisterListCreateView.as_view(), name='register-list-create'),
    path('register/<int:telegram_id>/', RegisterDetailView.as_view(), name='register-detail'),
]