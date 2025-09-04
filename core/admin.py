from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramGroup, Register, HemisTable


@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ['group_name', 'group_id', 'added_at', 'is_active', 'members_count']
    list_filter = ['is_active', 'added_at']
    search_fields = ['group_name', 'group_id']
    readonly_fields = ['added_at']
    
    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = 'A\'zolar soni'


@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ['fio', 'username', 'telegram_id', 'register_group', 'hemis_id', 'pnfl', 'is_active', 'is_teacher']
    list_filter = ['is_active', 'is_teacher', 'register_group', 'created']
    search_fields = ['fio', 'username', 'telegram_id', 'hemis_id', 'pnfl']
    readonly_fields = ['created', 'updated']
    list_editable = ['is_active', 'is_teacher']
    
    fieldsets = (
        ('Telegram Ma\'lumotlari', {
            'fields': ('telegram_id', 'username', 'register_group')
        }),
        ('Shaxsiy Ma\'lumotlar', {
            'fields': ('fio', 'hemis_id', 'pnfl')
        }),
        ('Aloqa Ma\'lumotlari', {
            'fields': ('tg_tel', 'tel', 'parent_tel', 'address')
        }),
        ('Holat', {
            'fields': ('is_active', 'is_teacher')
        }),
        ('Vaqt Ma\'lumotlari', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HemisTable)
class HemisTableAdmin(admin.ModelAdmin):
    list_display = ['fio', 'hemis_id', 'pnfl', 'course', 'student_group', 'register_status', 'groups_display']
    list_filter = ['course', 'created', 'register__is_active']
    search_fields = ['fio', 'hemis_id', 'pnfl', 'passport', 'student_group']
    readonly_fields = ['created', 'updated', 'register']
    filter_horizontal = ['telegram_groups']
    
    fieldsets = (
        ('Asosiy Ma\'lumotlar', {
            'fields': ('fio', 'hemis_id', 'pnfl', 'passport')
        }),
        ('Ta\'lim Ma\'lumotlari', {
            'fields': ('course', 'student_group', 'born')
        }),
        ('Bog\'lanish Ma\'lumotlari', {
            'fields': ('register', 'telegram_groups'),
            'description': 'Register va Telegram guruhlari avtomatik bog\'lanadi'
        }),
        ('Vaqt Ma\'lumotlari', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    def register_status(self, obj):
        if obj.register:
            if obj.register.is_active:
                return format_html('<span style="color: green;">✓ Faol</span>')
            else:
                return format_html('<span style="color: orange;">○ Nofaol</span>')
        return format_html('<span style="color: red;">✗ Bog\'lanmagan</span>')
    register_status.short_description = 'Register holati'
    
    def groups_display(self, obj):
        groups = obj.telegram_groups.all()
        if groups:
            group_names = [group.group_name or str(group.group_id) for group in groups[:3]]
            display_text = ', '.join(group_names)
            if groups.count() > 3:
                display_text += f' (+{groups.count() - 3} ko\'proq)'
            return display_text
        return 'Guruhsiz'
    groups_display.short_description = 'Telegram guruhlari'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

admin.site.site_header = "Masofaviy Ta'lim Admin Panel"
admin.site.site_title = "Masofaviy Ta'lim Admin"
admin.site.index_title = "Bosh sahifa"