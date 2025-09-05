# core/signals.py - Optimized Version

import logging
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from core.models import Register, HemisTable, TelegramGroup

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Register)
def link_register_with_hemis(sender, instance, created, **kwargs):
    """
    Register yaratilganda yoki yangilanganda:
    1. HemisTable bilan bog'lash
    2. Register ni faollashtirish
    3. HemisTable ni Register guruhlariga qo'shish
    """
    # Raw save yoki kerakli maydonlar bo'sh bo'lsa skip
    if kwargs.get('raw', False) or not instance.hemis_id or not instance.pnfl:
        return
        
    try:
        with transaction.atomic():
            # HemisTable da mos keluvchi yozuvni topish
            hemis_records = HemisTable.objects.filter(
                hemis_id=instance.hemis_id,
                pnfl=instance.pnfl
            )
            
            if not hemis_records.exists():
                logger.info(f"HemisTable topilmadi - Hemis ID: {instance.hemis_id}, PNFL: {instance.pnfl}")
                return
            
            # Birinchi bog'lanmagan yozuvni olish
            hemis_record = hemis_records.filter(register__isnull=True).first()
            
            if not hemis_record:
                # Agar bog'lanmagan topilmasa, birinchisini olish
                hemis_record = hemis_records.first()
                if hemis_record.register == instance:
                    # Allaqachon bog'langan
                    _sync_groups_for_register(instance, hemis_record)
                    return
            
            # HemisTable ni Register bilan bog'lash
            if hemis_record and not hemis_record.register:
                HemisTable.objects.filter(id=hemis_record.id).update(register=instance)
                logger.info(f"✅ HemisTable '{hemis_record.fio}' Register bilan bog'landi")
                
                # Register ni faollashtirish
                if not instance.is_active:
                    Register.objects.filter(id=instance.id).update(is_active=True)
                    logger.info(f"✅ Register '{instance}' faollashtirildi")
                
                # Guruhlarni sinxronlashtirish
                _sync_groups_for_register(instance, hemis_record)
                
    except Exception as e:
        logger.error(f"Register-HemisTable bog'lashda xato: {e}")


@receiver(post_save, sender=HemisTable)
def link_hemis_with_register(sender, instance, created, **kwargs):
    """
    HemisTable yaratilganda yoki yangilanganda:
    1. Register bilan bog'lash
    2. Register ni faollashtirish
    3. HemisTable ni Register guruhlariga qo'shish
    """
    # Raw save yoki yangi yaratilmagan bo'lsa yoki kerakli maydonlar bo'sh bo'lsa skip
    if kwargs.get('raw', False) or not created or not instance.hemis_id or not instance.pnfl:
        return
        
    try:
        with transaction.atomic():
            # Register da mos keluvchi yozuvni topish
            registers = Register.objects.filter(
                hemis_id=instance.hemis_id,
                pnfl=instance.pnfl
            )
            
            if not registers.exists():
                logger.info(f"Register topilmadi - Hemis ID: {instance.hemis_id}, PNFL: {instance.pnfl}")
                return
            
            # Birinchi nofaol yozuvni olish, aks holda birinchisini
            register = registers.filter(is_active=False).first()
            if not register:
                register = registers.first()
            
            # HemisTable ni Register bilan bog'lash
            if register and not instance.register:
                HemisTable.objects.filter(id=instance.id).update(register=register)
                logger.info(f"✅ HemisTable '{instance.fio}' Register bilan bog'landi")
                
                # Register ni faollashtirish
                if not register.is_active:
                    Register.objects.filter(id=register.id).update(is_active=True)
                    logger.info(f"✅ Register '{register}' faollashtirildi")
                
                # Guruhlarni sinxronlashtirish
                _sync_groups_for_hemis(register, instance)
                
    except Exception as e:
        logger.error(f"HemisTable-Register bog'lashda xato: {e}")


def _sync_groups_for_register(register_instance, hemis_record):
    """Register guruhlarini HemisTable bilan sinxronlashtirish"""
    try:
        # Register guruhlarini HemisTable ga qo'shish
        register_groups = register_instance.register_groups.filter(is_active=True)
        
        for group in register_groups:
            if not hemis_record.telegram_groups.filter(id=group.id).exists():
                hemis_record.telegram_groups.add(group)
                logger.info(f"✅ HemisTable '{hemis_record.fio}' guruhga qo'shildi: {group}")
                
    except Exception as e:
        logger.error(f"Register guruhlarini sinxronlashda xato: {e}")


def _sync_groups_for_hemis(register_instance, hemis_record):
    """HemisTable uchun Register guruhlarini sinxronlashtirish"""
    try:
        # Register guruhlarini HemisTable ga qo'shish
        register_groups = register_instance.register_groups.filter(is_active=True)
        
        for group in register_groups:
            if not hemis_record.telegram_groups.filter(id=group.id).exists():
                hemis_record.telegram_groups.add(group)
                logger.info(f"✅ HemisTable '{hemis_record.fio}' guruhga qo'shildi: {group}")
                
    except Exception as e:
        logger.error(f"HemisTable guruhlarini sinxronlashda xato: {e}")


@receiver(m2m_changed, sender=Register.register_groups.through)
def sync_register_groups_to_hemis(sender, instance, action, pk_set, **kwargs):
    """
    Register guruhlariga o'zgarish bo'lganda HemisTable ni ham yangilash
    """
    if action not in ['post_add', 'post_remove']:
        return
        
    try:
        # Register ga bog'langan HemisTable ni topish
        if hasattr(instance, 'hemis_data') and instance.hemis_data:
            hemis_record = instance.hemis_data
            
            if action == 'post_add' and pk_set:
                # Yangi guruhlarni qo'shish
                new_groups = TelegramGroup.objects.filter(
                    id__in=pk_set, 
                    is_active=True
                )
                
                for group in new_groups:
                    if not hemis_record.telegram_groups.filter(id=group.id).exists():
                        hemis_record.telegram_groups.add(group)
                        logger.info(f"✅ Yangi guruh qo'shildi: {group} -> {hemis_record.fio}")
            
            elif action == 'post_remove' and pk_set:
                # Guruhlarni olib tashlash
                hemis_record.telegram_groups.remove(*pk_set)
                logger.info(f"🗑️ Guruhlar olib tashlandi: {pk_set} -> {hemis_record.fio}")
                
    except Exception as e:
        logger.error(f"Register guruhlarini sinxronlashda xato: {e}")


@receiver(post_save, sender=TelegramGroup)
def update_group_status(sender, instance, created, **kwargs):
    """
    TelegramGroup nofaol qilinganda bog'langan yozuvlarni yangilash
    """
    if kwargs.get('raw', False) or created:
        return
        
    try:
        if not instance.is_active:
            # Nofaol guruh bilan bog'langan HemisTable larni topish
            affected_hemis = HemisTable.objects.filter(
                telegram_groups=instance
            )
            
            logger.info(f"📊 Nofaol guruh '{instance}' bilan bog'langan {affected_hemis.count()} ta HemisTable topildi")
            
            # Bu yerda kerak bo'lsa qo'shimcha ishlarni bajarish mumkin
            # Masalan, foydalanuvchilarni boshqa faol guruhga ko'chirish
            
    except Exception as e:
        logger.error(f"TelegramGroup holatini yangilashda xato: {e}")


# Logging konfiguratsiyasi
def setup_signals_logging():
    """Signals uchun logging sozlash"""
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


# Auto setup
setup_signals_logging()