from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AdminsCreationForm
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CustomLoginForm

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomLoginForm
    redirect_authenticated_user = False

    def get_initial(self):
        """Agar user login qilingan bo‘lsa, username inputni oldindan to‘ldirish"""
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial["username"] = self.request.user.username
        return initial

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")
        response = super().form_valid(form)

        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 hafta (14 kun)
        else:
            self.request.session.set_expiry(0)  # brauzer yopilganda sessiya tugaydi

        return response
    
    def form_invalid(self, form):
        if form.data.get("username") and form.data.get("password"):
            messages.error(self.request, "Login yoki parol xato!")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("main_view")


def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
@user_passes_test(lambda u: u.is_superadmin)
def add_admin(requset):
    if requset.method == "POST":
        form = AdminsCreationForm(requset.POST)
        if form.is_valid():
            form.save()
            return redirect("main_view")
        
        else:
            form = AdminsCreationForm()
        return render(requset, "accounts/add_admin.html", {"form": form})