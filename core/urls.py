from django.urls import path
from .views import (
    main_view, table_register, bulk_update_register, send_message_to_group,
    hemistable_view, mass_message_view, send_mass_message
    )

urlpatterns = [
    path('', main_view, name="main_view"),
    path('table_register/', table_register, name='table_register'),
    path('table_hemis/', hemistable_view, name='hemistable_view'),
    path('bulk_update_register/', bulk_update_register, name='bulk_update_register'),
    path('send-message/', send_message_to_group, name='send_message_to_group'),
    path('mass-message/', mass_message_view, name='mass_message'),
    path('send-mass-message/', send_mass_message, name='send_mass_message')
]