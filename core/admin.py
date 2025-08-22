from django.contrib import admin
from .models import TelegramGroup, Register, HemisTable

@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'group_id', 'added_at', 'is_active')
    list_filter = ('group_name', 'added_at')
    search_fields = ('group_name', 'added_at')
    readonly_fields = ('added_at', 'is_active')

@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'fio', 'register_group_id', 'created', 'updated')
    list_filter = ('register_group_id', 'created', 'updated')
    search_fields = ('username', 'fio', 'register_group_id')
    readonly_fields = ('created', 'updated')

@admin.register(HemisTable)
class HemisTableAdmin(admin.ModelAdmin):
    list_display = ('hemis_id', 'telegram_id', 'fio', 'course', 'major', 'student_group', 'created', 'updated')
    list_filter = ('course', 'major', 'student_group')
    search_fields = ('fio', 'major', 'student_group')
    readonly_fields = ('created', 'updated')

admin.site.site_header = "Masofaviy Ta'lim Admin Panel"
admin.site.site_title = "Masofaviy Ta'lim Admin"
admin.site.index_title = "Bosh sahifa"