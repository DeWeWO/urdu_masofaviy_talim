import json
from django.shortcuts import render, redirect
from .models import Register

def main_view(request):
    return render(request, 'core/index.html')

def table_register(request):
    reg_true = Register.objects.filter(is_active=True)
    teacher = Register.objects.filter(is_teacher=True)
    reg_false = Register.objects.filter(is_active=False, is_teacher=False)
    return render(request, 'core/pages/tables/tasdiqlash.html',
        {'reg_true': reg_true, 'teacher': teacher, 'reg_false': reg_false}
    )

def bulk_update_register(request):
    if request.method == 'POST':
        # Talabalar uchun
        active_ids = request.POST.getlist('active_students')
        # O'qituvchilar uchun
        teacher_ids = request.POST.getlist('teachers')
        
        try:
            # Avval barcha reg_false holatidagi ma'lumotlarni olish
            registers = Register.objects.filter(is_active=False, is_teacher=False)
            
            for register in registers:
                if str(register.id) in active_ids:
                    register.is_active = True
                    register.is_teacher = False
                elif str(register.id) in teacher_ids:
                    register.is_teacher = True
                    register.is_active = True
                
                register.save()
            
            return redirect('table_register')  # Sahifani qayta yuklash
            
        except Exception as e:
            return render(request, 'core/pages/tables/tasdiqlash.html', {
                'error': f'Xatolik yuz berdi: {str(e)}',
                'reg_false': Register.objects.filter(is_active=False, is_teacher=False)
            })
    
    return redirect('table_register')