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
    pnfl = models.CharField(max_length=25, null=True, blank=True, unique=False)
    tg_tel = models.CharField(max_length=15, null=True, blank=True)
    tel = models.CharField(max_length=15, null=True, blank=True)
    parent_tel = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.fio or str(self.telegram_id)

    class Meta:
        verbose_name = "Register"
        verbose_name_plural = "Registers"
        db_table = 'register'

class HemisTable(BaseModel):
    hemis_id = models.BigIntegerField(unique=True, db_index=True)
    telegram_id = models.OneToOneField(Register, on_delete=models.CASCADE, primary_key=True)
    fio = models.CharField(max_length=255)
    course = models.IntegerField()
    major = models.CharField(max_length=255)
    student_group = models.CharField(max_length=100)
    
    def __str__(self):
        return self.fio
    
    class Meta:
        verbose_name_plural = "Hemis Table"
        db_table = 'hemis_table'