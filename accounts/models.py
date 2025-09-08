from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["telegram_id"]
    
    objects = CustomUserManager()
    
    class Meta:
        db_table = "admins"
        verbose_name = "Admins"
        verbose_name_plural = "Admins"
    
    def __str__(self):
        return self.username