from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AdminsCreationForm
from .models import CustomUser

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect("main_view")
    return render(request, "accounts/login.html")

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