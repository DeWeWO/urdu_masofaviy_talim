from django.urls import path
from .views import CustomLoginView, LogoutView

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login_view"),
    path("logout/", LogoutView.as_view(), name="logout_view"),
]