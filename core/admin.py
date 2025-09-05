from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import TelegramGroup, Register, HemisTable


@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ['group_name', 'group_id', 'created', 'is_active', 'members_count']
    list_filter = ['is_active', 'created', 'updated']
    search_fields = ['group_name', 'group_id']
    readonly_fields = ['created', 'updated']
    ordering = ['-created']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            members_count=Count('members', distinct=True)
        )
    
    def members_count(self, obj):
        return obj.members_count
    members_count.admin_order_field = 'members_count'
    members_count.short_description = "A'zolar soni"


@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'username', 'telegram_id', 'hemis_id',
        'pnfl', 'groups_list', 'is_active', 'is_teacher', 'created'
    ]
    list_filter = [
        'is_active', 'is_teacher', 'created', 
        ('register_groups', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['fio', 'username', 'telegram_id', 'hemis_id', 'pnfl']
    readonly_fields = ['created', 'updated']
    list_editable = ['is_active', 'is_teacher']
    filter_horizontal = ['register_groups']
    list_per_page = 50
    ordering = ['-created']

    fieldsets = (
        ('Telegram Ma\'lumotlari', {
            'fields': ('telegram_id', 'username', 'register_groups'),
            'description': 'Telegram bot orqali olingan ma\'lumotlar'
        }),
        ('Shaxsiy Ma\'lumotlar', {
            'fields': ('fio', 'hemis_id', 'pnfl')
        }),
        ('Aloqa Ma\'lumotlari', {
            'fields': ('tg_tel', 'tel', 'parent_tel', 'address'),
            'classes': ('collapse',)
        }),
        ('Holat', {
            'fields': ('is_active', 'is_teacher')
        }),
        ('Vaqt Ma\'lumotlari', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('register_groups')

    def display_name(self, obj):
        name = obj.fio or obj.username or f"User {obj.telegram_id}"
        if obj.is_teacher:
            return format_html('<span style="color: blue; font-weight: bold;">👨‍🏫 {}</span>', name)
        return format_html('<span>{}</span>', name)
    display_name.short_description = "Ism"
    display_name.admin_order_field = 'fio'

    def groups_list(self, obj):
        groups = obj.register_groups.all()
        if not groups:
            return format_html('<span style="color: #999;">Guruhsiz</span>')
        
        group_names = []
        for group in groups[:2]:  # Show only first 2 groups
            name = group.group_name or str(group.group_id)
            if group.is_active:
                group_names.append(f'<span style="color: green;">{name}</span>')
            else:
                group_names.append(f'<span style="color: #999;">{name}</span>')
        
        display_text = ', '.join(group_names)
        if groups.count() > 2:
            display_text += f' <span style="color: #666;">(+{groups.count() - 2})</span>'
        
        return format_html(display_text)
    groups_list.short_description = "Telegram guruhlari"

    actions = ['activate_users', 'deactivate_users', 'mark_as_teachers']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} ta foydalanuvchi faollashtirildi.')
    activate_users.short_description = "Tanlangan foydalanuvchilarni faollashtirish"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} ta foydalanuvchi nofaollashtirildi.')
    deactivate_users.short_description = "Tanlangan foydalanuvchilarni nofaollashtirish"

    def mark_as_teachers(self, request, queryset):
        updated = queryset.update(is_teacher=True)
        self.message_user(request, f'{updated} ta foydalanuvchi o\'qituvchi qilib belgilandi.')
    mark_as_teachers.short_description = "Tanlangan foydalanuvchilarni o'qituvchi qilish"


@admin.register(HemisTable)
class HemisTableAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'hemis_id', 'pnfl', 'course', 
        'student_group', 'register_status', 'groups_display', 'created'
    ]
    list_filter = [
        'course', 'created', 'register__is_active',
        ('register', admin.RelatedOnlyFieldListFilter),
        ('telegram_groups', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['fio', 'hemis_id', 'pnfl', 'passport', 'student_group']
    readonly_fields = ['created', 'updated', 'register']
    filter_horizontal = ['telegram_groups']
    list_per_page = 50
    ordering = ['-created']
    
    fieldsets = (
        ('Asosiy Ma\'lumotlar', {
            'fields': ('fio', 'hemis_id', 'pnfl', 'passport', 'born')
        }),
        ('Ta\'lim Ma\'lumotlari', {
            'fields': ('course', 'student_group')
        }),
        ('Bog\'lanish Ma\'lumotlari', {
            'fields': ('register', 'telegram_groups'),
            'description': 'Register va Telegram guruhlari avtomatik bog\'lanadi',
            'classes': ('collapse',)
        }),
        ('Vaqt Ma\'lumotlari', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'register'
        ).prefetch_related('telegram_groups')

    def display_name(self, obj):
        return format_html('<strong>{}</strong>', obj.fio)
    display_name.short_description = "F.I.O"
    display_name.admin_order_field = 'fio'
    
    def register_status(self, obj):
        if not obj.register:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Bog\'lanmagan</span>'
            )
        
        if obj.register.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Faol</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">○ Nofaol</span>'
            )
    register_status.short_description = 'Register holati'
    register_status.admin_order_field = 'register__is_active'
    
    def groups_display(self, obj):
        groups = obj.telegram_groups.all()
        if not groups:
            return format_html('<span style="color: #999;">Guruhsiz</span>')
        
        group_names = []
        for group in groups[:2]:  # Show only first 2 groups
            name = group.group_name or str(group.group_id)
            if group.is_active:
                group_names.append(f'<span style="color: green;">{name}</span>')
            else:
                group_names.append(f'<span style="color: #999;">{name}</span>')
        
        display_text = ', '.join(group_names)
        if groups.count() > 2:
            display_text += f' <span style="color: #666;">(+{groups.count() - 2})</span>'
        
        return format_html(display_text)
    groups_display.short_description = 'Telegram guruhlari'

    actions = ['sync_with_register', 'clear_register_link']

    def sync_with_register(self, request, queryset):
        synced = 0
        for obj in queryset:
            obj._link_with_register()
            synced += 1
        self.message_user(request, f'{synced} ta yozuv Register bilan sinxronlashtirildi.')
    sync_with_register.short_description = "Register bilan sinxronlashtirish"

    def clear_register_link(self, request, queryset):
        updated = queryset.update(register=None)
        self.message_user(request, f'{updated} ta yozuvning Register bog\'lanishi tozalandi.')
    clear_register_link.short_description = "Register bog'lanishini tozalash"


# Admin site customization
admin.site.site_header = "Telegram Bot Admin Panel"
admin.site.site_title = "Telegram Bot Admin"
admin.site.index_title = "Boshqaruv paneli"
