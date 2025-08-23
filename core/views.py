from django.shortcuts import render

def main_view(request):
    return render(request, 'core/index.html')

def table_register(request):
    return render(request, 'core/pages/tables/tasdiqlash.html')