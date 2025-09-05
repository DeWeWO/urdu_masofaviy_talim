import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import datetime
from core.forms import ExcelUploadForm
from core.models import HemisTable, Register


def hemistable_view(request):
    """Hemis jadval ko'rish va Excel fayl yuklash"""
    
    if request.method == "POST":
        return handle_excel_upload(request)
    
    form = ExcelUploadForm()
    data = get_hemis_data()
    
    context = {
        "form": form,
        "data": data,
        "stats": get_statistics(data)
    }
    
    return render(request, 'core/pages/tables/hemis.html', context)


def handle_excel_upload(request):
    """Excel fayl yuklashni boshqarish"""
    form = ExcelUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        messages.error(request, "Fayl yuklashda xato yuz berdi")
        return redirect("hemistable_view")
    
    excel_file = request.FILES["file"]
    
    try:
        # Excel faylni o'qish
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        print(f"Excel ustunlari: {df.columns.tolist()}")
        print(f"Ma'lumotlar soni: {len(df)}")
        
        # Ma'lumotlarni saqlash
        result = process_excel_data(df)
        
        # Natijalarni ko'rsatish
        display_upload_results(request, result)
            
    except Exception as e:
        messages.error(request, f"❌ Excel xato: {str(e)}")
        print(f"Excel xato: {str(e)}")
    
    return redirect("hemistable_view")


@transaction.atomic
def process_excel_data(df):
    """Excel ma'lumotlarini qayta ishlash"""
    hemis_objects = []
    activated_registers = []
    errors = []
    
    # Mavjud hemis_id va pnfl larni olish
    existing_hemis_ids = set(HemisTable.objects.values_list('hemis_id', flat=True))
    existing_pnfls = set(
        HemisTable.objects.exclude(pnfl__isnull=True)
        .exclude(pnfl__exact='')
        .values_list('pnfl', flat=True)
    )
    
    for index, row in df.iterrows():
        try:
            # Excel ustunlarini moslashtirish
            hemis_id = get_cell_value(row, 0)        # A - Talaba ID
            fio = get_cell_value(row, 1)             # B - FIO
            born_value = get_cell_value(row, 8)      # I - Tug'ilgan sana
            pnfl = get_cell_value(row, 10)           # K - JSHSHIR
            passport = get_cell_value(row, 9)        # J - Pasport
            course = get_cell_value(row, 12)         # M - Kurs
            student_group = get_cell_value(row, 14)  # O - Guruh
            
            # Asosiy validatsiyalar
            validation_result = validate_row_data(
                index, hemis_id, fio, pnfl, passport, 
                existing_hemis_ids, existing_pnfls
            )
            
            if validation_result['error']:
                errors.append(validation_result['error'])
                continue
            
            # Ma'lumotlarni tozalash
            clean_data = clean_row_data(
                hemis_id, fio, born_value, pnfl, passport, course, student_group
            )
            
            # HemisTable obyekti yaratish
            hemis_objects.append(HemisTable(**clean_data))
            
            # Register bilan bog'lash uchun
            if clean_data['pnfl'] and len(clean_data['pnfl']) == 14:
                register_ids = check_register_activation(
                    clean_data['hemis_id'], clean_data['pnfl']
                )
                activated_registers.extend(register_ids)
            
            # Takrorlanishni oldini olish
            existing_hemis_ids.add(clean_data['hemis_id'])
            if clean_data['pnfl']:
                existing_pnfls.add(clean_data['pnfl'])
            
        except Exception as e:
            errors.append(f"Qator {index + 2}: {str(e)}")
            continue
    
    # Ma'lumotlarni saqlash
    created_count = save_hemis_objects(hemis_objects)
    activated_count = activate_registers(activated_registers)
    
    return {
        'created_count': created_count,
        'activated_count': activated_count,
        'errors': errors,
        'total_rows': len(df)
    }


def validate_row_data(index, hemis_id, fio, pnfl, passport, existing_hemis_ids, existing_pnfls):
    """Qator ma'lumotlarini validatsiya qilish"""
    row_num = index + 2
    
    # Hemis ID tekshiruvi
    if not hemis_id:
        return {'error': f"Qator {row_num}: Hemis ID bo'sh"}
    
    if str(hemis_id) in [str(x) for x in existing_hemis_ids]:
        return {'error': None}  # Skip, already exists
    
    # FIO tekshiruvi
    if not fio or len(str(fio).strip()) < 3:
        return {'error': f"Qator {row_num}: FIO bo'sh yoki juda qisqa"}
    
    # PNFL tekshiruvi
    if pnfl:
        clean_pnfl = ''.join(filter(str.isdigit, str(pnfl)))
        if clean_pnfl and len(clean_pnfl) != 14:
            return {'error': f"Qator {row_num}: PNFL 14 ta raqam bo'lishi kerak"}
        
        if clean_pnfl in existing_pnfls:
            return {'error': f"Qator {row_num}: PNFL allaqachon mavjud"}
    
    # Passport tekshiruvi
    if passport and len(str(passport).strip()) != 9:
        return {'error': f"Qator {row_num}: Passport 9 ta belgi bo'lishi kerak"}
    
    return {'error': None}


def clean_row_data(hemis_id, fio, born_value, pnfl, passport, course, student_group):
    """Qator ma'lumotlarini tozalash"""
    # PNFL ni tozalash
    clean_pnfl = ""
    if pnfl:
        pnfl_digits = ''.join(filter(str.isdigit, str(pnfl)))
        if len(pnfl_digits) == 14:
            clean_pnfl = pnfl_digits
    
    # Tug'ilgan sanani tozalash
    clean_born = None
    if born_value:
        try:
            # Agar sana formatida bo'lsa
            if isinstance(born_value, datetime):
                clean_born = born_value.date()
            else:
                # String formatdan parse qilish
                born_str = str(born_value).strip()
                if born_str and born_str != 'nan':
                    # Turli formatlarni sinab ko'rish
                    for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']:
                        try:
                            clean_born = datetime.strptime(born_str, fmt).date()
                            break
                        except ValueError:
                            continue
        except Exception:
            pass
    
    # Passport ni tozalash
    clean_passport = ""
    if passport:
        clean_passport = str(passport).strip().upper()
    
    return {
        'hemis_id': int(hemis_id),
        'fio': str(fio).strip(),
        'born': clean_born,
        'passport': clean_passport,
        'pnfl': clean_pnfl,
        'course': str(course).strip() if course else "",
        'student_group': str(student_group).strip() if student_group else "",
    }


def check_register_activation(hemis_id, pnfl):
    """Register faollashtirish uchun tekshirish"""
    try:
        registers = Register.objects.filter(
            hemis_id=hemis_id,
            pnfl=pnfl,
            is_active=False
        )
        return list(registers.values_list('id', flat=True))
    except Exception:
        return []


def save_hemis_objects(hemis_objects):
    """HemisTable obyektlarini saqlash"""
    if not hemis_objects:
        return 0
    
    try:
        # Validatsiya
        for obj in hemis_objects:
            obj.full_clean()
        
        # Bulk create
        HemisTable.objects.bulk_create(hemis_objects, ignore_conflicts=True)
        return len(hemis_objects)
        
    except ValidationError as e:
        print(f"Validatsiya xatosi: {e}")
        return 0
    except Exception as e:
        print(f"Saqlash xatosi: {e}")
        return 0


def activate_registers(register_ids):
    """Registerlarni faollashtirish"""
    if not register_ids:
        return 0
    
    try:
        return Register.objects.filter(
            id__in=list(set(register_ids))
        ).update(is_active=True)
    except Exception as e:
        print(f"Faollashtirish xatosi: {e}")
        return 0


def display_upload_results(request, result):
    """Upload natijalarini ko'rsatish"""
    created_count = result['created_count']
    activated_count = result['activated_count']
    errors = result['errors']
    total_rows = result['total_rows']
    
    # Xatolar
    if errors:
        error_count = len(errors)
        messages.warning(request, f"⚠️ {error_count} ta xato topildi")
        
        # Faqat dastlabki 3 ta xatoni ko'rsatish
        for error in errors[:3]:
            messages.error(request, error)
        
        if error_count > 3:
            messages.info(request, f"... va yana {error_count - 3} ta xato")
    
    # Muvaffaqiyatli natijalar
    if created_count > 0:
        messages.success(request, f"✅ {created_count} ta yangi yozuv qo'shildi")
        
    if activated_count > 0:
        messages.success(request, f"🔄 {activated_count} ta register faollashtirildi")
    
    # Umumiy ma'lumot
    processed_count = created_count + len(errors)
    if processed_count == 0:
        messages.info(request, "ℹ️ Hech qanday yangi ma'lumot topilmadi")
    else:
        success_rate = (created_count / processed_count) * 100 if processed_count > 0 else 0
        messages.info(
            request, 
            f"📊 Jami: {total_rows} qator, Qayta ishlandi: {processed_count}, "
            f"Muvaffaqiyat: {success_rate:.1f}%"
        )


def get_cell_value(row, column_index):
    """Hujayra qiymatini xavfsiz olish"""
    try:
        if column_index >= len(row):
            return ""
        
        value = row.iloc[column_index]
        
        # Bo'sh yoki NaN tekshirish
        if pd.isna(value) or value is None:
            return ""
        
        # String ga aylantirish va tozalash
        str_value = str(value).strip()
        
        # 'nan' stringni ham bo'sh deb hisoblash
        if str_value.lower() == 'nan':
            return ""
        
        return str_value
        
    except Exception as e:
        print(f"Hujayra olishda xato (ustun {column_index}): {e}")
        return ""


def get_hemis_data():
    """Hemis ma'lumotlarini optimallashtirilgan holda olish"""
    return (
        HemisTable.objects
        .select_related("register")
        .prefetch_related(
            "telegram_groups",
            "register__register_groups"
        )
        .order_by("-created")
    )


def get_statistics(data):
    """Kengaytirilgan statistika"""
    total_count = data.count()
    
    # Register statistikasi
    with_register = data.filter(register__isnull=False)
    registered_count = with_register.count()
    active_registered_count = with_register.filter(register__is_active=True).count()
    
    # Telegram guruh statistikasi
    in_group_count = data.filter(telegram_groups__isnull=False).distinct().count()
    
    return {
        'total_count': total_count,
        'registered_count': registered_count,
        'active_registered_count': active_registered_count,
        'in_group_count': in_group_count,
        'unregistered_count': total_count - registered_count,
        'inactive_registered_count': registered_count - active_registered_count,
        'not_in_group_count': total_count - in_group_count,
        'completion_rate': round((active_registered_count / total_count * 100), 1) if total_count > 0 else 0
    }