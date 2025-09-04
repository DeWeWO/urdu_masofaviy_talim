# core/signals.py - YANGI TO'LIQ VERSIYA

from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Register, HemisTable


@receiver(post_save, sender=Register)
def link_register_with_hemis(sender, instance, created, **kwargs):
    """
    Register yaratilganda yoki yangilanganda:
    1. HemisTable bilan bog'lash
    2. Register ni faollashtirish
    3. HemisTable ni Register guruhiga qo'shish
    """
    # Agar hemis_id yoki pnfl bo'sh bo'lsa, hech narsa qilmaymiz
    if not instance.hemis_id or not instance.pnfl:
        return
        
    try:
        # HemisTable da mos keluvchi yozuvni topish (hemis_id VA pnfl mos kelishi kerak)
        hemis_record = HemisTable.objects.get(
            hemis_id=instance.hemis_id,
            pnfl=instance.pnfl
        )
        
        # Agar HemisTable hali Register bilan bog'lanmagan bo'lsa
        if not hemis_record.register:
            # HemisTable ni Register bilan bog'lash
            hemis_record.register = instance
            hemis_record.save()
            
            print(f"✅ HemisTable '{hemis_record.fio}' Register bilan bog'landi")
            
        # Register ni faollashtirish
        if not instance.is_active:
            instance.is_active = True
            instance.save()
            print(f"✅ Register '{instance.fio}' faollashtirildi")
            
        # HemisTable ni Register guruhiga qo'shish
        if instance.register_group and not hemis_record.telegram_groups.filter(id=instance.register_group.id).exists():
            hemis_record.telegram_groups.add(instance.register_group)
            print(f"✅ HemisTable '{hemis_record.fio}' guruhga qo'shildi: {instance.register_group}")
                
    except HemisTable.DoesNotExist:
        # Mos keluvchi HemisTable topilmadi - bu normal holat
        print(f"ℹ️ Register uchun mos keluvchi HemisTable topilmadi - Hemis ID: {instance.hemis_id}, PNFL: {instance.pnfl}")
        pass
        
    except HemisTable.MultipleObjectsReturned:
        # Bir nechta mos keluvchi yozuv topilsa, birinchi bog'lanmagan yozuvni olish
        hemis_record = HemisTable.objects.filter(
            hemis_id=instance.hemis_id,
            pnfl=instance.pnfl,
            register__isnull=True  # Faqat bog'lanmaganlar
        ).first()
        
        if hemis_record:
            hemis_record.register = instance
            hemis_record.save()
            
            if not instance.is_active:
                instance.is_active = True
                instance.save()
                
            if instance.register_group and not hemis_record.telegram_groups.filter(id=instance.register_group.id).exists():
                hemis_record.telegram_groups.add(instance.register_group)
                
            print(f"✅ HemisTable '{hemis_record.fio}' Register bilan bog'landi (multiple ichidan)")


@receiver(post_save, sender=HemisTable)
def link_hemis_with_register(sender, instance, created, **kwargs):
    """
    HemisTable yaratilganda yoki yangilanganda:
    1. Register bilan bog'lash
    2. Register ni faollashtirish  
    3. HemisTable ni Register guruhiga qo'shish
    """
    # Agar yangi yaratilgan bo'lmasa yoki kerakli maydonlar bo'sh bo'lsa, hech narsa qilmaymiz
    if not created or not instance.hemis_id or not instance.pnfl:
        return
        
    try:
        # Register da mos keluvchi yozuvni topish (hemis_id VA pnfl mos kelishi kerak)
        register = Register.objects.get(
            hemis_id=instance.hemis_id,
            pnfl=instance.pnfl
        )
        
        # Agar HemisTable hali Register bilan bog'lanmagan bo'lsa
        if not instance.register:
            # HemisTable ni Register bilan bog'lash
            instance.register = register
            # Bu yerda save() chaqirmaslik kerak - cheksiz sikl bo'ladi
            HemisTable.objects.filter(id=instance.id).update(register=register)
            
            print(f"✅ HemisTable '{instance.fio}' Register bilan bog'landi")
            
        # Register ni faollashtirish
        if not register.is_active:
            register.is_active = True
            register.save()
            print(f"✅ Register '{register.fio}' faollashtirildi")
            
        # HemisTable ni Register guruhiga qo'shish
        if register.register_group and not instance.telegram_groups.filter(id=register.register_group.id).exists():
            instance.telegram_groups.add(register.register_group)
            print(f"✅ HemisTable '{instance.fio}' guruhga qo'shildi: {register.register_group}")
                
    except Register.DoesNotExist:
        # Mos keluvchi Register topilmadi - bu normal holat
        print(f"ℹ️ HemisTable uchun mos keluvchi Register topilmadi - Hemis ID: {instance.hemis_id}, PNFL: {instance.pnfl}")
        pass
        
    except Register.MultipleObjectsReturned:
        # Bir nechta mos keluvchi yozuv topilsa, birinchi nofaol yozuvni olish
        register = Register.objects.filter(
            hemis_id=instance.hemis_id,
            pnfl=instance.pnfl,
            is_active=False  # Birinchi nofaol yozuvni olish
        ).first()
        
        # Agar nofaol topilmasa, birinchi topilganini olish
        if not register:
            register = Register.objects.filter(
                hemis_id=instance.hemis_id,
                pnfl=instance.pnfl
            ).first()
        
        if register and not instance.register:
            HemisTable.objects.filter(id=instance.id).update(register=register)
            
            if not register.is_active:
                register.is_active = True
                register.save()
                
            if register.register_group and not instance.telegram_groups.filter(id=register.register_group.id).exists():
                instance.telegram_groups.add(register.register_group)
                
            print(f"✅ HemisTable '{instance.fio}' Register bilan bog'landi (multiple ichidan)")