from django.urls import path
from .views import main_view, table_register, bulk_update_register

urlpatterns = [
    path('', main_view, name="main_view"),
    path('register/table/', table_register, name='table_register'),
    path('bulk-update-register/', bulk_update_register, name='bulk_update_register'),
]