from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import TelegramGroup, Register, HemisTable, MemberActivity



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


@admin.register(MemberActivity)
class MemberActivityAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_info', 'group_info', 'activity_badge', 
        'action_info', 'admin_info', 'activity_time', 'created_at'
    ]
    list_filter = [
        'activity_type', 'action_by', 'telegram_group__group_name',
        'activity_time', 'created_at'
    ]
    search_fields = [
        'register__fio', 'register__username', 'register__telegram_id',
        'telegram_group__group_name', 'admin_name', 'admin_username'
    ]
    readonly_fields = [
        'created_at', 'user_display_info', 'group_display_info', 
        'admin_display_info', 'activity_summary'
    ]
    fieldsets = (
        ('Asosiy Ma\'lumotlar', {
            'fields': (
                'register', 'telegram_group', 'activity_type', 'action_by', 'activity_time'
            )
        }),
        ('Admin Ma\'lumotlari', {
            'fields': (
                'admin_telegram_id', 'admin_name', 'admin_username'
            ),
            'classes': ['collapse'],
        }),
        ('Qo\'shimcha', {
            'fields': (
                'notes', 'created_at'
            ),
            'classes': ['collapse'],
        }),
        ('Ko\'rinish', {
            'fields': (
                'user_display_info', 'group_display_info', 
                'admin_display_info', 'activity_summary'
            ),
            'classes': ['collapse'],
        }),
    )
    
    # Sahifalash
    list_per_page = 50
    
    # Default ordering
    ordering = ['-activity_time']
    
    # Filter sidebar
    list_filter = [
        ('activity_type', admin.ChoicesFieldListFilter),
        ('action_by', admin.ChoicesFieldListFilter),
        'telegram_group',
        ('activity_time', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
    ]
    
    def user_info(self, obj):
        """Foydalanuvchi ma'lumotlarini ko'rsatish"""
        user_name = obj.register.fio or f"User {obj.register.telegram_id}"
        username = f"@{obj.register.username}" if obj.register.username else ""
        
        return format_html(
            '<div style="min-width: 150px;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}<br>ID: {}</small>'
            '</div>',
            user_name,
            username,
            obj.register.telegram_id
        )
    user_info.short_description = "Foydalanuvchi"
    user_info.admin_order_field = 'register__fio'
    
    def group_info(self, obj):
        """Guruh ma'lumotlarini ko'rsatish"""
        return format_html(
            '<div style="min-width: 120px;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">ID: {}</small>'
            '</div>',
            obj.telegram_group.group_name,
            obj.telegram_group.group_id
        )
    group_info.short_description = "Guruh"
    group_info.admin_order_field = 'telegram_group__group_name'
    
    def activity_badge(self, obj):
        """Faoliyat turi badgesi"""
        colors = {
            'join': '#28a745',      # Yashil
            'leave': '#ffc107',     # Sariq
            'kicked': '#dc3545',    # Qizil
            'removed': '#fd7e14',   # Orange
        }
        
        color = colors.get(obj.activity_type, '#6c757d')
        
        return format_html(
            '<span style="display: inline-block; padding: 3px 8px; '
            'background-color: {}; color: white; border-radius: 12px; '
            'font-size: 11px; font-weight: bold; text-transform: uppercase;">'
            '{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_badge.short_description = "Faoliyat"
    activity_badge.admin_order_field = 'activity_type'
    
    def action_info(self, obj):
        """Kim tomonidan amalga oshirilgani"""
        icons = {
            'self': '👤',
            'admin': '👨‍💼', 
            'system': '🤖',
            'invite_link': '🔗',
        }
        
        icon = icons.get(obj.action_by, '❓')
        
        return format_html(
            '<div style="min-width: 100px;">'
            '{} {}'
            '</div>',
            icon,
            obj.get_action_by_display()
        )
    action_info.short_description = "Kim tomonidan"
    action_info.admin_order_field = 'action_by'
    
    def admin_info(self, obj):
        """Admin ma'lumotlari"""
        if obj.action_by == 'admin' and (obj.admin_name or obj.admin_username or obj.admin_telegram_id):
            admin_name = obj.admin_name or f"ID: {obj.admin_telegram_id}"
            admin_username = f"@{obj.admin_username}" if obj.admin_username else ""
            
            return format_html(
                '<div style="min-width: 120px;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}</small>'
                '</div>',
                admin_name,
                admin_username
            )
        return format_html('<span style="color: #ccc;">-</span>')
    admin_info.short_description = "Admin"
    
    def user_display_info(self, obj):
        """Foydalanuvchi to'liq ma'lumotlari (readonly)"""
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            '<h4>👤 Foydalanuvchi Ma\'lumotlari</h4>'
            '<p><strong>Ism:</strong> {}</p>'
            '<p><strong>Username:</strong> {}</p>'
            '<p><strong>Telegram ID:</strong> {}</p>'
            '</div>',
            obj.register.fio or "Kiritilmagan",
            f"@{obj.register.username}" if obj.register.username else "Yo'q",
            obj.register.telegram_id
        )
    user_display_info.short_description = "Foydalanuvchi Ma'lumotlari"
    
    def group_display_info(self, obj):
        """Guruh to'liq ma'lumotlari (readonly)"""
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            '<h4>💬 Guruh Ma\'lumotlari</h4>'
            '<p><strong>Nomi:</strong> {}</p>'
            '<p><strong>Group ID:</strong> {}</p>'
            '</div>',
            obj.telegram_group.group_name,
            obj.telegram_group.group_id
        )
    group_display_info.short_description = "Guruh Ma'lumotlari"
    
    def admin_display_info(self, obj):
        """Admin to'liq ma'lumotlari (readonly)"""
        if obj.action_by == 'admin':
            return format_html(
                '<div style="padding: 10px; background: #fff3cd; border-radius: 5px;">'
                '<h4>👨‍💼 Admin Ma\'lumotlari</h4>'
                '<p><strong>Ism:</strong> {}</p>'
                '<p><strong>Username:</strong> {}</p>'
                '<p><strong>Telegram ID:</strong> {}</p>'
                '</div>',
                obj.admin_name or "Kiritilmagan",
                f"@{obj.admin_username}" if obj.admin_username else "Yo'q",
                obj.admin_telegram_id or "Kiritilmagan"
            )
        return format_html('<p style="color: #666;">Admin ma\'lumotlari mavjud emas</p>')
    admin_display_info.short_description = "Admin Ma'lumotlari"
    
    def activity_summary(self, obj):
        """Faoliyat xulosasi (readonly)"""
        colors = {
            'join': '#d4edda',
            'leave': '#fff3cd', 
            'kicked': '#f8d7da',
            'removed': '#ffeaa7',
        }
        
        return format_html(
            '<div style="padding: 15px; background: {}; border-radius: 8px; border-left: 4px solid #007bff;">'
            '<h4>📊 Faoliyat Xulosasi</h4>'
            '<p><strong>Foydalanuvchi:</strong> {} guruhdan {}</p>'
            '<p><strong>Vaqt:</strong> {}</p>'
            '<p><strong>Usul:</strong> {}</p>'
            '<p><strong>Izoh:</strong> {}</p>'
            '</div>',
            colors.get(obj.activity_type, '#f8f9fa'),
            obj.user_display_name,
            obj.get_activity_type_display().lower(),
            obj.activity_time.strftime('%Y-%m-%d %H:%M:%S'),
            obj.get_action_by_display(),
            obj.notes or "Yo'q"
        )
    activity_summary.short_description = "Faoliyat Xulosasi"
    
    def get_queryset(self, request):
        """Optimized queryset with select_related"""
        return super().get_queryset(request).select_related(
            'register', 'telegram_group'
        )
    
    def changelist_view(self, request, extra_context=None):
        """Admin panel ro'yxat sahifasiga statistika qo'shish"""
        # Statistikani hisoblash
        total_count = self.get_queryset(request).count()
        join_count = self.get_queryset(request).filter(activity_type='join').count()
        leave_count = self.get_queryset(request).filter(
            activity_type__in=['leave', 'kicked', 'removed']
        ).count()
        
        # Oxirgi 24 soat statistikasi
        from datetime import timedelta
        last_24h = timezone.now() - timedelta(hours=24)
        recent_count = self.get_queryset(request).filter(
            activity_time__gte=last_24h
        ).count()
        
        extra_context = extra_context or {}
        extra_context['custom_stats'] = {
            'total_count': total_count,
            'join_count': join_count,
            'leave_count': leave_count,
            'recent_count': recent_count,
        }
        
        return super().changelist_view(request, extra_context)


# Custom filters
class RecentActivityFilter(admin.SimpleListFilter):
    title = 'Oxirgi faoliyat'
    parameter_name = 'recent_activity'
    
    def lookups(self, request, model_admin):
        return (
            ('1h', 'Oxirgi 1 soat'),
            ('24h', 'Oxirgi 24 soat'),
            ('7d', 'Oxirgi 7 kun'),
            ('30d', 'Oxirgi 30 kun'),
        )
    
    def queryset(self, request, queryset):
        from datetime import timedelta
        now = timezone.now()
        
        if self.value() == '1h':
            return queryset.filter(activity_time__gte=now - timedelta(hours=1))
        elif self.value() == '24h':
            return queryset.filter(activity_time__gte=now - timedelta(hours=24))
        elif self.value() == '7d':
            return queryset.filter(activity_time__gte=now - timedelta(days=7))
        elif self.value() == '30d':
            return queryset.filter(activity_time__gte=now - timedelta(days=30))


# Admin site customization
admin.site.site_header = "Telegram Bot Admin Panel"
admin.site.site_title = "Telegram Bot Admin"
admin.site.index_title = "Boshqaruv paneli"
