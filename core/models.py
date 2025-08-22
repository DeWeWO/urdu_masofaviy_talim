from django.db import models

class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class TelegramGroup(models.Model):
    group_name = models.CharField(max_length=100)
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
    username = models.CharField(max_length=100)
    fio = models.CharField(max_length=255, null=True)
    register_group_id = models.BigIntegerField(unique=True, db_index=True)
    pnfl = models.BigIntegerField(unique=True, null=True)
    tg_tel = models.CharField(max_length=15, null=True)
    tel = models.CharField(max_length=15, null=True)
    parent_tel = models.CharField(max_length=15, null=True)
    address = models.CharField(max_length=255, null=True)
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.fio
    
    class Meta:
        verbose_name_plural = "Register"
        db_table = 'register'
