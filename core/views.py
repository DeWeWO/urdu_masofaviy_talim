from django.shortcuts import render
from .models import Register

def main_view(request):
    return render(request, 'core/index.html')

def table_register(request):
    reg = Register.objects.all()
    return render(request, 'core/pages/tables/tasdiqlash.html', {'reg': reg})
