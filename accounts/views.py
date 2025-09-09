from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AdminsCreationForm
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from .forms import CustomLoginForm

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomLoginForm
    redirect_authenticated_user = False

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial["username"] = self.request.user.username
        return initial

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")
        response = super().form_valid(form)

        if remember_me:
            self.request.session.set_expiry(1209600)
        else:
            self.request.session.set_expiry(0)

        return response
    
    def form_invalid(self, form):
        if form.data.get("username") and form.data.get("password"):
            messages.error(self.request, "Login yoki parol xato!")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("main_view")


class LogoutView(View):
    def get(self, request):
        logout(request=request)
        return redirect("login_view")
