import io
import json
import logging
import requests
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from core.models import Register, TelegramGroup
from environs import Env

# Matplotlib sozlamalari
matplotlib.use("Agg")
plt.rcParams["font.family"] = ["DejaVu Sans", "Arial", "sans-serif"]
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'Liberation Sans']
# Unicode xatolarini oldini olish
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# Logger sozlash
logger = logging.getLogger(__name__)

# Environment o'zgaruvchilari
env = Env()
env.read_env()
BOT_TOKEN = env.str('BOT_TOKEN')


class TelegramAPIClient:
    """Telegram API bilan ishlash uchun alohida klass"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, chat_id, text, parse_mode="HTML"):
        """Oddiy xabar yuborish"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, data=payload, timeout=30)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram xabar yuborishda xato: {str(e)}")
            return {"ok": False, "description": str(e)}
    
    def send_photo(self, chat_id, photo_bytes, caption=None):
        """Rasm yuborish"""
        try:
            url = f"{self.base_url}/sendPhoto"
            files = {"photo": ("table.png", photo_bytes, "image/png")}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            
            response = requests.post(url, data=data, files=files, timeout=30)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram rasm yuborishda xato: {str(e)}")
            return {"ok": False, "description": str(e)}


class DataFrameImageGenerator:
    """DataFrame ni rasm formatiga aylantirish uchun klass"""
    
    @staticmethod
    def clean_text_for_display(text):
        """Maxsus belgilarni tozalash"""
        if not text:
            return text
        
        # Maxsus Unicode belgilarni oddiy harflarga almashtirish
        replacements = {
            '\u1D0F': 'o',  # LATIN LETTER SMALL CAPITAL O
            '\u1D0D': 'm',  # LATIN LETTER SMALL CAPITAL M  
            '\u1D20': 'v',  # LATIN LETTER SMALL CAPITAL V
            '\u1D18': 'p',  # LATIN LETTER SMALL CAPITAL P
            '\u1D00': 'a',  # LATIN LETTER SMALL CAPITAL A
            '\u1D07': 'e',  # LATIN LETTER SMALL CAPITAL E
            '\u026A': 'i',  # LATIN LETTER SMALL CAPITAL I
            '\u1D1C': 'u',  # LATIN LETTER SMALL CAPITAL U
        }
        
        # Almashtirish
        cleaned_text = str(text)
        for old_char, new_char in replacements.items():
            cleaned_text = cleaned_text.replace(old_char, new_char)
        
        # ASCII bo'lmagan belgilarni tozalash
        try:
            cleaned_text = cleaned_text.encode('ascii', 'ignore').decode('ascii')
        except:
            pass
            
        return cleaned_text
    
    @staticmethod
    def create_table_image(df, figsize=None):
        """DataFrame dan PNG rasm yaratish"""
        if df.empty:
            return None
        
        # Ma'lumotlarni tozalash
        cleaned_df = df.copy()
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':
                cleaned_df[col] = cleaned_df[col].apply(
                    lambda x: DataFrameImageGenerator.clean_text_for_display(x)
                )
        
        # Ustun nomlarini ham tozalash
        cleaned_columns = [
            DataFrameImageGenerator.clean_text_for_display(col) 
            for col in cleaned_df.columns
        ]
        cleaned_df.columns = cleaned_columns
        
        # O'lchamni hisoblash
        if figsize is None:
            width = max(8, len(cleaned_df.columns) * 1.5)
            height = max(2, len(cleaned_df) * 0.5 + 1)
            figsize = (width, height)
        
        try:
            fig, ax = plt.subplots(figsize=figsize)
            ax.axis("off")
            
            # Jadval yaratish
            table = ax.table(
                cellText=cleaned_df.values,
                colLabels=cleaned_df.columns,
                cellLoc="center",
                loc="center"
            )
            
            # Jadval sozlamalari
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            
            # Sarlavha stilini o'zgartirish
            for i in range(len(cleaned_df.columns)):
                table[(0, i)].set_facecolor('#4472C4')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            # Rasmni bufferga saqlash
            buf = io.BytesIO()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plt.savefig(buf, format="png", bbox_inches="tight", dpi=150)
            buf.seek(0)
            plt.close(fig)  # xotirani tozalash
            
            return buf.getvalue()
            
        except Exception as e:
            logger.error(f"Rasm yaratishda xato: {str(e)}")
            plt.close('all')  # Barcha figuralarni yopish
            return None


class RegisterService:
    """Register modeli bilan ishlash uchun service klass"""
    
    @staticmethod
    def get_users_by_criteria(target, group=None):
        """Kriteriyalar asosida foydalanuvchilarni olish"""
        base_query = Register.objects.all()
        
        if group:
            base_query = base_query.filter(register_group=group)
        
        if target == "reg_true":
            return base_query.filter(is_active=True, is_teacher=False)
        elif target == "reg_false":
            return base_query.filter(is_active=False, is_teacher=False)
        elif target == "teacher":
            return base_query.filter(is_teacher=True)
        else:
            return Register.objects.none()
    
    @staticmethod
    def bulk_update_status(group_id, active_ids, teacher_ids):
        """Ko'plab foydalanuvchilarni yangilash"""
        try:
            # Guruhni tekshirish
            if group_id:
                group = TelegramGroup.objects.get(id=group_id)
                base_query = Register.objects.filter(register_group=group)
            else:
                base_query = Register.objects.all()
            
            updated_count = 0
            
            # Faol talabalarni yangilash
            if active_ids:
                updated = base_query.filter(
                    id__in=active_ids,
                    is_active=False,
                    is_teacher=False
                ).update(is_active=True, is_teacher=False)
                updated_count += updated
            
            # O'qituvchilarni yangilash
            if teacher_ids:
                updated = base_query.filter(
                    id__in=teacher_ids
                ).update(is_teacher=True, is_active=True)
                updated_count += updated
            
            return {"success": True, "updated_count": updated_count}
            
        except ObjectDoesNotExist:
            return {"success": False, "error": "Guruh topilmadi"}
        except Exception as e:
            logger.error(f"Bulk update xatosi: {str(e)}")
            return {"success": False, "error": str(e)}


class MessageSender:
    """Xabar yuborish logikasini boshqaruvchi klass"""
    
    def __init__(self):
        self.telegram_client = TelegramAPIClient(BOT_TOKEN)
        self.image_generator = DataFrameImageGenerator()
    
    def send_to_users(self, users, message, method="private", group_chat_id=None):
        """Foydalanuvchilarga xabar yuborish"""
        if method == "private":
            return self._send_private_messages(users, message)
        elif method == "group" and group_chat_id:
            return self._send_group_message_with_table(users, message, group_chat_id)
        else:
            return {"sent": 0, "failed": 1, "total": 1, "errors": ["Noto'g'ri parametrlar"]}
    
    def _send_private_messages(self, users, message):
        """Har bir foydalanuvchiga alohida xabar yuborish"""
        sent = 0
        failed = 0
        errors = []
        
        for user in users:
            if not user.telegram_id:
                failed += 1
                errors.append(f"{user.fio}: Telegram ID yo'q")
                continue
            
            result = self.telegram_client.send_message(user.telegram_id, message)
            
            if result.get("ok"):
                sent += 1
                logger.info(f"Xabar yuborildi: {user.fio} ({user.telegram_id})")
            else:
                failed += 1
                error_desc = result.get("description", "Noma'lum xato")
                errors.append(f"{user.fio}: {error_desc}")
                logger.warning(f"Xabar yuborilmadi: {user.fio} - {error_desc}")
        
        return {
            "sent": sent,
            "failed": failed,
            "total": users.count(),
            "method": "Private Messages",
            "errors": errors[:10]  # Faqat birinchi 10 ta xatoni ko'rsatish
        }
    
    def _send_group_message_with_table(self, users, message, group_chat_id):
        """Guruhga xabar va jadval yuborish"""
        try:
            # Foydalanuvchilar jadvalini yaratish
            user_data = []
            for idx, user in enumerate(users, 1):
                user_data.append([
                    idx, 
                    user.fio or "Noma'lum", 
                    user.username or "---"
                ])
            
            if user_data:
                df = pd.DataFrame(user_data, columns=["#", "F.I.O", "Username"])
                image_bytes = self.image_generator.create_table_image(df)
                
                if image_bytes:
                    # Rasmli xabar yuborish
                    result = self.telegram_client.send_photo(group_chat_id, image_bytes, message)
                else:
                    # Faqat matn yuborish
                    result = self.telegram_client.send_message(group_chat_id, message)
            else:
                # Foydalanuvchilar yo'q bo'lsa faqat xabar yuborish
                result = self.telegram_client.send_message(group_chat_id, message)
            
            if result.get("ok"):
                logger.info(f"Guruhga xabar yuborildi: {group_chat_id}")
                return {
                    "sent": 1,
                    "failed": 0,
                    "total": 1,
                    "method": "Group Message"
                }
            else:
                error_desc = result.get("description", "Noma'lum xato")
                logger.warning(f"Guruhga xabar yuborilmadi: {group_chat_id} - {error_desc}")
                return {
                    "sent": 0,
                    "failed": 1,
                    "total": 1,
                    "method": "Group Message",
                    "errors": [f"Guruh {group_chat_id}: {error_desc}"]
                }
                
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {str(e)}")
            return {
                "sent": 0,
                "failed": 1,
                "total": 1,
                "method": "Group Message",
                "errors": [str(e)]
            }


# ========================= VIEW FUNCTIONS =========================

def main_view(request):
    """Asosiy sahifa"""
    return render(request, 'core/index.html')


def table_register(request):
    """
    Ro'yxatga olish jadvali - guruhlarni ko'rsatish va filterlash
    """
    groups = TelegramGroup.objects.filter(is_active=True)
    group_id = request.GET.get("group_id")
    
    context = {
        "groups": groups,
        "selected_group": None,
        "reg_true": Register.objects.none(),
        "reg_false": Register.objects.none(),
        "teacher": Register.objects.none(),
    }
    
    if group_id:
        try:
            selected_group = TelegramGroup.objects.get(id=group_id, is_active=True)
            context.update({
                "selected_group": selected_group,
                "reg_true": RegisterService.get_users_by_criteria("reg_true", selected_group),
                "reg_false": RegisterService.get_users_by_criteria("reg_false", selected_group),
                "teacher": RegisterService.get_users_by_criteria("teacher", selected_group),
            })
        except ObjectDoesNotExist:
            messages.error(request, "Tanlangan guruh topilmadi yoki faol emas")
    
    return render(request, "core/pages/tables/tasdiqlash.html", context)


def bulk_update_register(request):
    """
    Ko'plab foydalanuvchilarni bir vaqtda yangilash
    """
    if request.method != 'POST':
        return redirect('table_register')
    
    group_id = request.POST.get('group_id')
    active_ids = request.POST.getlist('active_students')
    teacher_ids = request.POST.getlist('teachers')
    
    # Yangilash operatsiyasini bajarish
    result = RegisterService.bulk_update_status(group_id, active_ids, teacher_ids)
    
    if result["success"]:
        messages.success(request, f"{result['updated_count']} ta foydalanuvchi muvaffaqiyatli yangilandi")
    else:
        messages.error(request, f"Xatolik yuz berdi: {result['error']}")
    
    # Redirect qilish
    if group_id:
        return redirect(f'/table_register/?group_id={group_id}')
    return redirect('table_register')


@csrf_exempt
def send_message_to_group(request):
    """
    Tanlangan guruhga yoki foydalanuvchilarga xabar yuborish
    """
    if request.method != "POST":
        return JsonResponse({"error": "Faqat POST so'rovlar qabul qilinadi"})
    
    # Parametrlarni olish
    target = request.POST.get("target")
    method = request.POST.get("method")
    message = request.POST.get("message")
    group_id = request.POST.get("group_id")
    
    # Validatsiya
    if not all([target, method, message]):
        return JsonResponse({"error": "Barcha majburiy maydonlarni to'ldiring"})
    
    if method == "group" and not group_id:
        return JsonResponse({"error": "Guruh ID ni kiriting"})
    
    # Guruhni tekshirish (agar group_id mavjud bo'lsa)
    selected_group = None
    if group_id:
        try:
            selected_group = TelegramGroup.objects.get(id=group_id, is_active=True)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Tanlangan guruh topilmadi yoki faol emas"})
    
    # Foydalanuvchilarni olish
    users = RegisterService.get_users_by_criteria(target, selected_group)
    
    if not users.exists():
        return JsonResponse({
            "error": "Tanlangan kriteriyalarga mos foydalanuvchilar topilmadi"
        })
    
    # Xabar yuborish
    message_sender = MessageSender()
    
    if method == "group":
        # Guruh chat ID ni modeldan olish (group_id field)
        group_chat_id = selected_group.group_id if selected_group else group_id
        result = message_sender.send_to_users(
            users, message, method="group", group_chat_id=group_chat_id
        )
    else:
        result = message_sender.send_to_users(users, message, method="private")
    
    return JsonResponse(result)


# ========================= LEGACY SUPPORT FUNCTIONS =========================

def dataframe_to_image(df):
    """
    DataFrame dan PNG rasm yaratish (legacy function)
    """
    if df.empty:
        return None
    
    generator = DataFrameImageGenerator()
    return generator.create_table_image(df)


def send_telegram_message(chat_id, text, image_bytes=None):
    """
    Legacy function - backward compatibility uchun
    """
    client = TelegramAPIClient(BOT_TOKEN)
    
    if image_bytes:
        return client.send_photo(chat_id, image_bytes, text)
    else:
        return client.send_message(chat_id, text)


def send_telegram_photo(chat_id, photo_buf, caption=None):
    """
    Legacy function - backward compatibility uchun
    """
    client = TelegramAPIClient(BOT_TOKEN)
    return client.send_photo(chat_id, photo_buf, caption)


def generate_table_image(data, columns):
    """
    Legacy function - list data dan rasm yaratish
    """
    if not data:
        return None
        
    df = pd.DataFrame(data, columns=columns)
    generator = DataFrameImageGenerator()
    
    image_bytes = generator.create_table_image(df)
    if image_bytes:
        return io.BytesIO(image_bytes)
    return None


def send_private_messages(users, message):
    """
    Legacy function - backward compatibility uchun
    """
    sender = MessageSender()
    return sender._send_private_messages(users, message)


def send_group_message(group_chat_id, message):
    """
    Legacy function - backward compatibility uchun
    """
    client = TelegramAPIClient(BOT_TOKEN)
    result = client.send_message(group_chat_id, message)
    
    if result.get("ok"):
        return {
            "sent": 1,
            "failed": 0,
            "total": 1,
            "method": "Group Message"
        }
    else:
        error_desc = result.get("description", "Noma'lum xato")
        return {
            "sent": 0,
            "failed": 1,
            "total": 1,
            "method": "Group Message",
            "errors": [f"Guruh {group_chat_id}: {error_desc}"]
        }