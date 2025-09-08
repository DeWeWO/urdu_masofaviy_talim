from django.urls import path
from .views import login_view, logout_view, add_admin

urlpatterns = [
    path("login/", login_view, name="login_view"),
    path("logout/", logout_view, name="logout_view"),
    path("add_admin/", add_admin, name="add_admin"),
]