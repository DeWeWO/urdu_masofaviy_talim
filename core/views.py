import json
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Register, TelegramGroup
from environs import Env
import logging

# Logger sozlash
logger = logging.getLogger(__name__)

env = Env()
env.read_env()

BOT_TOKEN = env.str('BOT_TOKEN')

def main_view(request):
    return render(request, 'core/index.html')

def table_register(request):
    """
    Tasdiqlash sahifasi - guruhlarni ko'rsatish va filterlash
    """
    groups = TelegramGroup.objects.all()
    group_id = request.GET.get("group_id")

    reg_true = []
    reg_false = []
    teacher = []
    selected_group = None

    if group_id:
        try:
            selected_group = TelegramGroup.objects.get(id=group_id)
            reg_true = Register.objects.filter(is_active=True, register_group=selected_group)
            reg_false = Register.objects.filter(is_active=False, is_teacher=False, register_group=selected_group)
            teacher = Register.objects.filter(is_teacher=True, register_group=selected_group)
        except TelegramGroup.DoesNotExist:
            messages.error(request, "Bunday guruh topilmadi")

    return render(request, "core/pages/tables/tasdiqlash.html", {
        "groups": groups,
        "selected_group": selected_group,
        "reg_true": reg_true,
        "reg_false": reg_false,
        "teacher": teacher,
    })

def bulk_update_register(request):
    """
    Ko'plab foydalanuvchilarni bir vaqtda yangilash
    """
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        active_ids = request.POST.getlist('active_students')
        teacher_ids = request.POST.getlist('teachers')
        
        try:
            if group_id:
                # Faqat tanlangan guruh bo'yicha filterlash
                selected_group = TelegramGroup.objects.get(id=group_id)
                registers = Register.objects.filter(
                    is_active=False, 
                    is_teacher=False, 
                    register_group=selected_group
                )
            else:
                registers = Register.objects.filter(is_active=False, is_teacher=False)
            
            updated_count = 0
            for register in registers:
                if str(register.id) in active_ids:
                    register.is_active = True
                    register.is_teacher = False
                    register.save()
                    updated_count += 1
                elif str(register.id) in teacher_ids:
                    register.is_teacher = True
                    register.is_active = True
                    register.save()
                    updated_count += 1
            
            messages.success(request, f"{updated_count} ta foydalanuvchi muvaffaqiyatli yangilandi")
            
            if group_id:
                return redirect(f'/table_register/?group_id={group_id}')
            return redirect('table_register')
            
        except Exception as e:
            logger.error(f"Bulk update error: {str(e)}")
            messages.error(request, f'Xatolik yuz berdi: {str(e)}')
            
            if group_id:
                return redirect(f'/table_register/?group_id={group_id}')
            return redirect('table_register')
    
    return redirect('table_register')

@csrf_exempt
def send_message_to_group(request):
    """
    Telegram bot orqali xabar yuborish
    """
    if request.method != "POST":
        return JsonResponse({"error": "Faqat POST so'rov qabul qilinadi"}, status=405)

    try:
        target = request.POST.get("target")
        method = request.POST.get("method")
        message = request.POST.get("message")
        group_id = request.POST.get("group_id")

        # Validatsiya
        if not all([target, method, message, group_id]):
            return JsonResponse({"error": "Barcha maydonlarni to'ldiring"}, status=400)

        if not message.strip():
            return JsonResponse({"error": "Xabar matni bo'sh bo'lishi mumkin emas"}, status=400)

        # Guruhni tekshirish
        try:
            selected_group = TelegramGroup.objects.get(id=group_id)
        except TelegramGroup.DoesNotExist:
            return JsonResponse({"error": "Guruh topilmadi"}, status=404)

        # Xabar yuborish usuli bo'yicha
        if method == "private":
            # Private chatga har bir foydalanuvchiga alohida yuborish
            
            # Foydalanuvchilarni tanlash
            if target == "reg_true":
                users = Register.objects.filter(is_active=True, register_group=selected_group)
            elif target == "teacher":
                users = Register.objects.filter(is_teacher=True, register_group=selected_group)
            elif target == "reg_false":
                users = Register.objects.filter(
                    is_active=False, 
                    is_teacher=False, 
                    register_group=selected_group
                )
            else:
                return JsonResponse({"error": "Noto'g'ri tanlov qilindi"}, status=400)

            if not users.exists():
                return JsonResponse({"error": "Bu guruhda tanlangan kategoriyada foydalanuvchilar topilmadi"}, status=404)

            result = send_private_messages(users, message)
            
        elif method == "group":
            # Guruh chatiga bitta xabar yuborish
            if not selected_group.group_id:
                return JsonResponse({"error": "Bu guruhning Telegram chat ID si mavjud emas"}, status=400)
            
            result = send_group_message(selected_group.group_id, message)
            
        else:
            return JsonResponse({"error": "Noto'g'ri yuborish usuli tanlandi"}, status=400)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        return JsonResponse({"error": f"Server xatosi: {str(e)}"}, status=500)

def send_private_messages(users, message):
    """
    Har bir foydalanuvchiga alohida private chat orqali xabar yuborish
    """
    success_count = 0
    fail_count = 0
    errors = []

    for user in users:
        if user.telegram_id:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": user.telegram_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                
                response = requests.post(url, data=payload, timeout=30)
                resp_json = response.json()
                
                if resp_json.get("ok"):
                    success_count += 1
                else:
                    fail_count += 1
                    error_desc = resp_json.get("description", "Noma'lum xato")
                    errors.append(f"User {user.telegram_id}: {error_desc}")
                    
            except requests.exceptions.Timeout:
                fail_count += 1
                errors.append(f"User {user.telegram_id}: Timeout")
            except Exception as e:
                fail_count += 1
                errors.append(f"User {user.telegram_id}: {str(e)}")

    result = {
        "sent": success_count,
        "failed": fail_count,
        "total": users.count(),
        "method": "Private Messages"
    }
    
    if errors:
        result["errors"] = errors[:5]  # Faqat birinchi 5 ta xatoni ko'rsatish

    return result

def send_group_message(group_chat_id, message):
    """
    Guruh chatiga bitta xabar yuborish
    """
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": group_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, data=payload, timeout=30)
        resp_json = response.json()
        
        if resp_json.get("ok"):
            return {
                "sent": 1,
                "failed": 0,
                "total": 1,
                "method": "Group Message"
            }
        else:
            error_desc = resp_json.get("description", "Noma'lum xato")
            return {
                "sent": 0,
                "failed": 1,
                "total": 1,
                "method": "Group Message",
                "errors": [f"Group {group_chat_id}: {error_desc}"]
            }
            
    except requests.exceptions.Timeout:
        return {
            "sent": 0,
            "failed": 1,
            "total": 1,
            "method": "Group Message",
            "errors": [f"Group {group_chat_id}: Timeout"]
        }
    except Exception as e:
        return {
            "sent": 0,
            "failed": 1,
            "total": 1,
            "method": "Group Message",
            "errors": [f"Group {group_chat_id}: {str(e)}"]
        }