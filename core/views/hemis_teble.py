import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
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
        created_count, activated_count, errors = process_excel_simple(df)
        
        # Natijalarni ko'rsatish
        if errors:
            messages.warning(request, f"Xatolar: {len(errors)} ta")
            for error in errors[:5]:  # Faqat 5 ta ko'rsatish
                messages.error(request, error)
        
        if created_count > 0:
            messages.success(request, f"✅ {created_count} ta yangi yozuv qo'shildi")
        else:
            messages.info(request, "ℹ️ Yangi ma'lumotlar qo'shilmadi")
            
        if activated_count > 0:
            messages.success(request, f"🔄 {activated_count} ta register faollashtirildi")
            
    except Exception as e:
        messages.error(request, f"❌ Excel xato: {str(e)}")
        print(f"Excel xato: {str(e)}")  # Debug
    
    return redirect("hemistable_view")


def process_excel_simple(df):
    """ODDIY: Ma'lumotlarni borligicha olish"""
    hemis_objects = []
    activated_registers = []
    errors = []
    
    # Mavjud ID larni olish
    existing_ids = set(HemisTable.objects.values_list('hemis_id', flat=True))
    
    for index, row in df.iterrows():
        try:
            # USTUN TARTIBINI SHUBU YERDA SOZLANG:
            # Excel da qaysi ustunda qaysi ma'lumot bo'lsa, o'sha indeksni yozing
            
            hemis_id = get_cell_value(row, 0)        # A ustuni - Talaba ID
            fio = get_cell_value(row, 1)             # B ustuni - FIO
            born_value = get_cell_value(row, 8)      # C ustuni - Tug'ilgan sana (qanday kelsa o'shanday)
            pnfl = get_cell_value(row, 10)            # D ustuni - JSHSHIR
            passport = get_cell_value(row, 9)        # E ustuni - Pasport
            course = get_cell_value(row, 12)          # F ustuni - Kurs
            student_group = get_cell_value(row, 14)   # G ustuni - Guruh
            
            # Asosiy tekshiruvlar
            if not hemis_id:
                errors.append(f"Qator {index + 2}: ID bo'sh")
                continue
                
            if str(hemis_id) in [str(x) for x in existing_ids]:
                continue  # Allaqachon mavjud
                
            if not fio:
                errors.append(f"Qator {index + 2}: FIO bo'sh")
                continue
            
            # PNFL ni tozalash (faqat raqamlar)
            clean_pnfl_value = ""
            if pnfl:
                pnfl_digits = ''.join(filter(str.isdigit, str(pnfl)))
                if len(pnfl_digits) == 14:
                    clean_pnfl_value = pnfl_digits
                else:
                    clean_pnfl_value = str(pnfl).strip()
            
            # Obyekt yaratish
            hemis_objects.append(HemisTable(
                hemis_id=str(hemis_id).strip(),
                fio=str(fio).strip(),
                born=str(born_value).strip() if born_value else "",  # STRING sifatida saqlash
                passport=str(passport).strip() if passport else "",
                pnfl=clean_pnfl_value,
                course=str(course).strip() if course else "",
                student_group=str(student_group).strip() if student_group else "",
            ))
            
            # Register faollashtirish
            if clean_pnfl_value and len(clean_pnfl_value) == 14:
                try:
                    register = Register.objects.filter(
                        hemis_id=str(hemis_id).strip(),
                        pnfl=clean_pnfl_value,
                        is_active=False
                    ).first()
                    if register:
                        activated_registers.append(register.id)
                except Exception:
                    pass
            
            existing_ids.add(str(hemis_id).strip())
            
        except Exception as e:
            errors.append(f"Qator {index + 2}: {str(e)}")
            print(f"Qator {index + 2} xato: {e}")  # Debug
            continue
    
    # Saqlash
    created_count = 0
    if hemis_objects:
        try:
            HemisTable.objects.bulk_create(hemis_objects, ignore_conflicts=True)
            created_count = len(hemis_objects)
            print(f"Saqlandi: {created_count} ta")  # Debug
        except Exception as e:
            errors.append(f"Saqlashda xato: {str(e)}")
            print(f"Saqlash xato: {e}")  # Debug
    
    # Register faollashtirish
    activated_count = 0
    if activated_registers:
        try:
            activated_count = Register.objects.filter(
                id__in=activated_registers
            ).update(is_active=True)
            print(f"Faollashtirildi: {activated_count} ta")  # Debug
        except Exception as e:
            errors.append(f"Faollashtirish xato: {str(e)}")
    
    return created_count, activated_count, errors


def get_cell_value(row, column_index):
    """Hujayra qiymatini olish - oddiy usul"""
    try:
        if column_index < len(row):
            value = row.iloc[column_index]
            
            # Bo'sh yoki NaN tekshirish
            if pd.isna(value) or value is None:
                return ""
            
            # String ga aylantirish va tozalash
            return str(value).strip()
        
        return ""
    except Exception as e:
        print(f"Hujayra olishda xato: {e}")  # Debug
        return ""


def get_hemis_data():
    """Ma'lumotlarni olish"""
    return HemisTable.objects.select_related(
        'register', 
        'register__register_group'
    ).prefetch_related(
        'telegram_groups'
    ).order_by('-created')


def get_statistics(data):
    """Statistika"""
    total_count = data.count()
    registered_count = data.filter(register__isnull=False).count()
    in_group_count = data.filter(telegram_groups__isnull=False).distinct().count()
    
    return {
        'total_count': total_count,
        'registered_count': registered_count,
        'in_group_count': in_group_count,
        'unregistered_count': total_count - registered_count,
        'not_in_group_count': total_count - in_group_count
    }