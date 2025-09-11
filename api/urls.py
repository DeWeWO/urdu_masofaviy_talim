from django.urls import path
from accounts.views import check_admin
from .views import (
    add_telegram_group, RegisterListCreateView, RegisterDetailView, get_all_users_basic_info,
    check_user_status, get_users_by_status, get_user_by_telegram_id, MemberActivityCreateView,
    MemberActivityListView, member_activity_stats, get_user_info
    )

urlpatterns = [
    path('telegram/group/add/', add_telegram_group, name='add_telegram_group'),
    path('register/', RegisterListCreateView.as_view(), name='register-list-create'),
    path('register/<int:telegram_id>/', RegisterDetailView.as_view(), name='register-detail'),
    path('users/<int:telegram_id>/', get_user_by_telegram_id, name='get_user_by_telegram_id'),
    path('users/basic-info/', get_all_users_basic_info, name='get_all_users_basic_info'),
    path('users/check-status/<int:telegram_id>/', check_user_status, name='check_user_status'),
    path('users/by-status/', get_users_by_status, name='get_users_by_status'),
    path('member-activity/add/', MemberActivityCreateView.as_view(), name='member-activity-create'),
    path('member-activity/list/', MemberActivityListView.as_view(), name='member-activity-list'),
    path('member-activity/stats/', member_activity_stats, name='member-activity-stats'),
    path("user-info/", get_user_info, name="user-info"),
    path("check-admin/", check_admin, name="check_admin"),
]