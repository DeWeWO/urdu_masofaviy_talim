from django.urls import path
from .views import main_view, table_register, bulk_update_register, send_message_to_group

urlpatterns = [
    path('', main_view, name="main_view"),
    path('register/table/', table_register, name='table_register'),
    path('bulk_update_register/', bulk_update_register, name='bulk_update_register'),
    path('send-message/', send_message_to_group, name='send_message_to_group'),
]