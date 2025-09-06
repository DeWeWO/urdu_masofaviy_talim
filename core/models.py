from django.db import models
from django.core.exceptions import ValidationError


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class TelegramGroup(BaseModel):
    group_name = models.CharField(max_length=200, null=True, blank=True)
    group_id = models.BigIntegerField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.group_name or 'Unknown'} ({self.group_id})"
    
    class Meta:
        db_table = 'telegram_group'
        verbose_name = 'Telegram Group'
        verbose_name_plural = 'Telegram Groups'


class Register(BaseModel):
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    fio = models.CharField(max_length=255, null=True, blank=True)
    register_groups = models.ManyToManyField(
        TelegramGroup, 
        related_name="members", 
        blank=True
    )
    hemis_id = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True)
    pnfl = models.CharField(max_length=14, null=True, blank=True, unique=True, db_index=True)
    tg_tel = models.CharField(max_length=15, null=True, blank=True)
    tel = models.CharField(max_length=15, null=True, blank=True)
    parent_tel = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)  # TextField for longer addresses
    is_active = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return self.fio or self.username or str(self.telegram_id)

    def clean(self):
        # PNFL validation
        if self.pnfl and len(self.pnfl) != 14:
            raise ValidationError({'pnfl': 'PNFL must be exactly 14 digits'})
        
        # Phone number validation
        for field_name in ['tg_tel', 'tel', 'parent_tel']:
            phone = getattr(self, field_name)
            if phone and not phone.replace('+', '').replace(' ', '').replace('-', '').isdigit():
                raise ValidationError({field_name: 'Invalid phone number format'})

    class Meta:
        db_table = 'register'
        verbose_name = "Register"
        verbose_name_plural = "Registers"
        indexes = [
            models.Index(fields=['telegram_id', 'is_active']),
            models.Index(fields=['hemis_id', 'pnfl']),
        ]


class HemisTable(BaseModel):
    register = models.OneToOneField(
        "Register",
        on_delete=models.SET_NULL,  # CASCADE
        null=True, blank=True,
        related_name='hemis_data'
    )
    telegram_groups = models.ManyToManyField(
        TelegramGroup,
        blank=True,
        related_name='hemis_members'
    )
    hemis_id = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True)
    fio = models.CharField(max_length=255)
    born = models.DateField(null=True, blank=True)
    passport = models.CharField(null=True, blank=True, max_length=9, unique=True)
    pnfl = models.CharField(null=True, blank=True, max_length=14, unique=True, db_index=True)
    course = models.CharField(max_length=100)
    student_group = models.CharField(max_length=255)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self._link_with_register()
    
    def _link_with_register(self):
        """Link HemisTable with Register based on hemis_id and pnfl"""
        if not self.hemis_id or not self.pnfl:
            return
            
        try:
            register = Register.objects.select_related().get(
                hemis_id=self.hemis_id,
                pnfl=self.pnfl
            )
            
            # Link with register if not already linked
            if not self.register:
                self.register = register
                HemisTable.objects.filter(id=self.id).update(register=register)
                
                # Activate register if not active
                if not register.is_active:
                    Register.objects.filter(id=register.id).update(is_active=True)
            
            # Sync telegram groups
            self._sync_telegram_groups(register)
                
        except Register.DoesNotExist:
            pass  # No matching register found
        except Register.MultipleObjectsReturned:
            # Handle multiple matches - take the first active one
            register = Register.objects.filter(
                hemis_id=self.hemis_id,
                pnfl=self.pnfl,
                is_active=True
            ).first()
            
            if not register:
                register = Register.objects.filter(
                    hemis_id=self.hemis_id,
                    pnfl=self.pnfl
                ).first()
            
            if register and not self.register:
                self.register = register
                HemisTable.objects.filter(id=self.id).update(register=register)
                
                if not register.is_active:
                    Register.objects.filter(id=register.id).update(is_active=True)
                    
                self._sync_telegram_groups(register)
    
    def _sync_telegram_groups(self, register):
        """Sync telegram groups between register and hemis table"""
        # Add register groups to hemis table
        for group in register.register_groups.all():
            if not self.telegram_groups.filter(id=group.id).exists():
                self.telegram_groups.add(group)
    
    def clean(self):
        # PNFL validation
        if self.pnfl and len(self.pnfl) != 14:
            raise ValidationError({'pnfl': 'PNFL must be exactly 14 digits'})
        
        # Passport validation
        if self.passport and len(self.passport) != 9:
            raise ValidationError({'passport': 'Passport must be exactly 9 characters'})
    
    def __str__(self):
        return f"{self.fio} ({self.hemis_id})"
    
    class Meta:
        db_table = 'hemis_table'
        verbose_name = "Hemis Record"
        verbose_name_plural = "Hemis Records"
        indexes = [
            models.Index(fields=['hemis_id', 'pnfl']),
            models.Index(fields=['fio', 'student_group']),
        ]

class MemberActivity(models.Model):
    """Guruh a'zolari faoliyati (kirish/chiqish) modeli"""
    
    class ActivityType(models.TextChoices):
        JOIN = 'join', 'Kirdi'
        LEAVE = 'leave', 'Chiqdi'
        KICKED = 'kicked', 'Chiqarildi'
        REMOVED = 'removed', 'O\'chirildi'
    
    class ActionBy(models.TextChoices):
        SELF = 'self', 'O\'zi'
        ADMIN = 'admin', 'Admin'
        SYSTEM = 'system', 'Tizim'
        INVITE_LINK = 'invite_link', 'Invite Link'
    
    # Foreign Key fields
    register = models.ForeignKey(
        'Register', 
        on_delete=models.CASCADE,
        related_name='activities',
        help_text="Foydalanuvchi ma'lumotlari"
    )
    telegram_group = models.ForeignKey(
        'TelegramGroup', 
        on_delete=models.CASCADE,
        related_name='member_activities',
        help_text="Telegram guruh ma'lumotlari"
    )
    
    # Activity details
    activity_type = models.CharField(
        max_length=10,
        choices=ActivityType.choices,
        help_text="Faoliyat turi (kirdi/chiqdi/chiqarildi)"
    )
    action_by = models.CharField(
        max_length=15,
        choices=ActionBy.choices,
        help_text="Kim tomonidan amalga oshirildi"
    )
    
    # Admin who performed action (optional)
    admin_telegram_id = models.BigIntegerField(
        null=True, 
        blank=True,
        help_text="Actionni amalga oshirgan admin telegram ID si"
    )
    admin_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Admin ismi"
    )
    admin_username = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Admin username"
    )
    
    # Timestamps
    activity_time = models.DateTimeField(
        help_text="Telegram eventdan kelgan vaqt"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Database ga yozilgan vaqt"
    )
    
    # Additional info
    notes = models.TextField(
        blank=True,
        help_text="Qo'shimcha ma'lumotlar"
    )
    
    class Meta:
        db_table = 'member_activities'
        verbose_name = 'A\'zo faoliyati'
        verbose_name_plural = 'A\'zolar faoliyati'
        ordering = ['-activity_time']
        indexes = [
            models.Index(fields=['register', 'activity_time']),
            models.Index(fields=['telegram_group', 'activity_time']),
            models.Index(fields=['activity_type', 'activity_time']),
        ]
    
    def __str__(self):
        return f"{self.register.fio or self.register.telegram_id} - {self.get_activity_type_display()} - {self.telegram_group.group_name}"
    
    @property
    def user_display_name(self):
        """Foydalanuvchi nomini qaytarish"""
        return self.register.fio or f"User {self.register.telegram_id}"
    
    @property
    def admin_display_name(self):
        """Admin nomini qaytarish"""
        if self.admin_name:
            return self.admin_name
        elif self.admin_username:
            return f"@{self.admin_username}"
        elif self.admin_telegram_id:
            return f"ID: {self.admin_telegram_id}"
        return "Noma'lum"