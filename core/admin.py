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
    list_display = ('hemis_id', 'fio', 'born', 'passport', 'pnfl', 'course', 'student_group', 'in_group', 'get_register', 'created', 'updated')
    list_filter = ('course', 'student_group', 'in_group', 'born')
    search_fields = ('fio', 'student_group', 'passport', 'pnfl')
    readonly_fields = ('created', 'updated')
    ordering = ('-created',)
    
    def get_register(self, obj):
        return obj.register if obj.register else "Belgilanmagan"
    get_register.short_description = "Register"

admin.site.site_header = "Masofaviy Ta'lim Admin Panel"
admin.site.site_title = "Masofaviy Ta'lim Admin"
admin.site.index_title = "Bosh sahifa"