import json
import mimetypes
import urllib.request
import urllib.parse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import TelegramGroup
import os
from environs import Env
#   
env = Env()
env.read_env()

def mass_message_view(request):
    groups = TelegramGroup.objects.filter(is_active=True)
    return render(request, 'core/pages/tables/tg_guruh.html', {'groups': groups})

def send_telegram_request(method, data=None, files=None):
    bot_token = env.str('BOT_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    
    if files:
        boundary = '----WebKitFormBoundary' + ''.join(['%02x' % b for b in os.urandom(16)])
        body = b''
        
        # Add text fields
        if data:
            for key, value in data.items():
                body += f'--{boundary}\r\n'.encode()
                body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                body += f'{value}\r\n'.encode()
        
        # Add file
        for field_name, (filename, file_data, content_type) in files.items():
            body += f'--{boundary}\r\n'.encode()
            body += f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
            body += f'Content-Type: {content_type}\r\n\r\n'.encode()
            body += file_data
            body += b'\r\n'
        
        body += f'--{boundary}--\r\n'.encode()
        
        req = urllib.request.Request(url, data=body)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    else:
        if data:
            data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def get_telegram_method(file_type):
    """Fayl turiga qarab Telegram metodini aniqlash"""
    if file_type.startswith('image/'):
        return 'sendPhoto', 'photo'
    elif file_type.startswith('video/'):
        return 'sendVideo', 'video'
    elif file_type.startswith('audio/'):
        return 'sendAudio', 'audio'
    else:
        return 'sendDocument', 'document'

@csrf_exempt
def send_mass_message(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        group_ids = request.POST.getlist('group_ids')
        message_text = request.POST.get('message_text', '').strip()
        files_data = request.FILES.getlist('files')
        
        print(f"Debug: Groups: {group_ids}")
        print(f"Debug: Message: {message_text}")
        print(f"Debug: Files count: {len(files_data)}")
        
        if not group_ids:
            return JsonResponse({'success': False, 'error': 'Guruhlar tanlanmagan'})
        
        if not message_text and not files_data:
            return JsonResponse({'success': False, 'error': 'Matn yoki fayl kiritilishi kerak'})
        
        # Bot tokenni tekshirish
        bot_token = getattr(settings, 'BOT_TOKEN', None)
        if not bot_token or bot_token == 'your_bot_token_here':
            return JsonResponse({'success': False, 'error': 'BOT_TOKEN sozlanmagan'})
        
        # Bot validligini tekshirish
        test_result = send_telegram_request('getMe')
        if not test_result.get('ok'):
            return JsonResponse({'success': False, 'error': f'Bot token xato: {test_result.get("error", "Unknown")}'})
        
        print(f"Debug: Bot info: {test_result.get('result', {}).get('username', 'Unknown')}")
        
        successful_sends = 0
        failed_sends = 0
        errors = []
        
        for group_id in group_ids:
            try:
                group = TelegramGroup.objects.get(group_id=group_id, is_active=True)
                print(f"Debug: Processing group: {group.group_name} ({group_id})")
                
                # Fayllarni yuborish
                if files_data:
                    for i, file_obj in enumerate(files_data):
                        file_content = file_obj.read()
                        file_obj.seek(0)  # Reset file pointer
                        file_name = file_obj.name
                        content_type = file_obj.content_type or mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
                        
                        print(f"Debug: Sending file {file_name} ({content_type}) to {group_id}")
                        
                        method, field_name = get_telegram_method(content_type)
                        
                        files = {field_name: (file_name, file_content, content_type)}
                        data = {'chat_id': str(group_id)}
                        
                        # Birinchi faylga caption qo'shish
                        if i == 0 and message_text:
                            data['caption'] = message_text
                        
                        result = send_telegram_request(method, data, files)
                        if not result.get('ok'):
                            error_msg = result.get('description', result.get('error', 'Noma\'lum xatolik'))
                            raise Exception(f"Fayl yuborishda xatolik: {error_msg}")
                
                # Agar fayllar yo'q va faqat matn bor bo'lsa
                elif message_text:
                    print(f"Debug: Sending text message to {group_id}")
                    data = {
                        'chat_id': str(group_id),
                        'text': message_text,
                        'parse_mode': 'HTML'
                    }
                    result = send_telegram_request('sendMessage', data)
                    if not result.get('ok'):
                        error_msg = result.get('description', result.get('error', 'Noma\'lum xatolik'))
                        raise Exception(f"Xabar yuborishda xatolik: {error_msg}")
                
                successful_sends += 1
                print(f"Debug: Successfully sent to {group.group_name}")
                
            except TelegramGroup.DoesNotExist:
                failed_sends += 1
                errors.append(f"Guruh topilmadi: {group_id}")
                print(f"Debug: Group not found: {group_id}")
            except Exception as e:
                failed_sends += 1
                error_msg = str(e)
                errors.append(f"{group.group_name}: {error_msg}")
                print(f"Debug: Error for {group.group_name}: {error_msg}")
        
        return JsonResponse({
            'success': True,
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'errors': errors[:5]  # Faqat birinchi 5 ta xatolikni ko'rsatish
        })
        
    except Exception as e:
        print(f"Debug: General error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})