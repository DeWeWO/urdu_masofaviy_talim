from django.urls import path
from .views import (
    add_telegram_group, RegisterListCreateView, RegisterDetailView, get_all_users_basic_info,
    check_user_status, get_users_by_status, get_user_by_telegram_id
    )

urlpatterns = [
    path('telegram/group/add/', add_telegram_group, name='add_telegram_group'),
    path('register/', RegisterListCreateView.as_view(), name='register-list-create'),
    path('register/<int:telegram_id>/', RegisterDetailView.as_view(), name='register-detail'),
    path('users/<int:telegram_id>/', get_user_by_telegram_id, name='get_user_by_telegram_id'),

    # Barcha foydalanuvchilarning telegram_id va pnfl larini olish
    path('users/basic-info/', get_all_users_basic_info, name='get_all_users_basic_info'),
    
    # Foydalanuvchi holatini tekshirish
    path('users/check-status/<int:telegram_id>/', check_user_status, name='check_user_status'),
    
    # Status bo'yicha foydalanuvchilar
    path('users/by-status/', get_users_by_status, name='get_users_by_status'),
]