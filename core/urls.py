from django.urls import path
from .views import (
    main_view, table_register, bulk_update_register, send_message_to_group,
    hemistable_view
    )

urlpatterns = [
    path('', main_view, name="main_view"),
    path('table_register/', table_register, name='table_register'),
    path('table_hemis/', hemistable_view, name='hemistable_view'),
    path('bulk_update_register/', bulk_update_register, name='bulk_update_register'),
    path('send-message/', send_message_to_group, name='send_message_to_group'),
]