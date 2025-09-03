from django.db import models

class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class TelegramGroup(models.Model):
    group_name = models.CharField(max_length=100, null=True, blank=True)
    group_id = models.BigIntegerField(unique=True, db_index=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.group_name} ({self.group_id})"
    
    class Meta:
        db_table = 'telegram_group'
        verbose_name = 'Telegram Group'
        verbose_name_plural = 'Telegram Groups'

class Register(BaseModel):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    fio = models.CharField(max_length=255, null=True, blank=True)
    register_group = models.ForeignKey(TelegramGroup, on_delete=models.CASCADE, related_name="members")
    hemis_id = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True)
    pnfl = models.CharField(max_length=25, null=True, blank=True, unique=False)
    tg_tel = models.CharField(max_length=15, null=True, blank=True)
    tel = models.CharField(max_length=15, null=True, blank=True)
    parent_tel = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return self.fio or str(self.telegram_id)

    class Meta:
        db_table = 'register'
        verbose_name = "Register"
        verbose_name_plural = "Registers"

class HemisTable(BaseModel):
    register = models.OneToOneField(
        "Register",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='hemis_data'
    )
    hemis_id = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True)
    fio = models.CharField(max_length=255)
    born = models.DateField(null=True, blank=True)
    passport = models.CharField(max_length=9)
    pnfl = models.CharField(max_length=14, db_index=True)
    course = models.CharField(max_length=100)
    student_group = models.CharField(max_length=255)
    in_group = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.fio} ({self.hemis_id})"
    
    class Meta:
        db_table = 'hemis_table'
        verbose_name = "Hemis Record"
        verbose_name_plural = "Hemis Table"

