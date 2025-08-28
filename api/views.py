from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import TelegramGroup, Register
from .serializers import TelegramGroupSerializers, RegisterSerializer, RegisterDetailSerializer

@api_view(['POST'])
def add_telegram_group(request):
    serializers = TelegramGroupSerializers(data=request.data)
    if serializers.is_valid():
        group = serializers.save()
        return Response({
            'success': True,
            'message': 'Group added successfully',
            'group_id': group.group_id,
            'group_name': group.group_name
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializers.errors
    }, status=status.HTTP_400_BAD_REQUEST)

class RegisterListCreateView(generics.ListCreateAPIView):
    queryset = Register.objects.all()
    serializer_class = RegisterSerializer

class RegisterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RegisterSerializer
    lookup_field = 'telegram_id'
    
    def get_queryset(self):
        return Register.objects.all()


@api_view(['GET'])
def get_all_users_basic_info(request):
    """
    Barcha foydalanuvchilarning telegram_id va pnfl ma'lumotlarini qaytaradi
    """
    try:
        users = Register.objects.all().values('telegram_id', 'pnfl')
        users_list = list(users)
        
        return Response({
            'success': True,
            'data': users_list,
            'count': len(users_list)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def check_user_status(request, telegram_id):
    """
    Telegram ID bo'yicha foydalanuvchi holatini tekshiradi
    """
    try:
        user = Register.objects.filter(telegram_id=telegram_id).first()
        
        if not user:
            return Response({
                'success': True,
                'status': 'not_registered',
                'message': 'Foydalanuvchi topilmadi',
                'action': 'register'
            }, status=status.HTTP_200_OK)
        
        elif not user.pnfl:
            return Response({
                'success': True,
                'status': 'incomplete_registration',
                'message': 'Registratsiya yakunlanmagan',
                'action': 'complete_register',
                'user_data': {
                    'telegram_id': user.telegram_id,
                    'username': user.username,
                    'fio': user.fio
                }
            }, status=status.HTTP_200_OK)
        
        else:
            return Response({
                'success': True,
                'status': 'registered',
                'message': 'Foydalanuvchi ro\'yxatdan o\'tgan',
                'action': 'update_info',
                'user_data': {
                    'telegram_id': user.telegram_id,
                    'username': user.username,
                    'fio': user.fio,
                    'pnfl': user.pnfl,
                    'tg_tel': user.tg_tel,
                    'tel': user.tel,
                    'parent_tel': user.parent_tel,
                    'address': user.address,
                    'is_active': user.is_active,
                    'is_teacher': user.is_teacher
                }
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_users_by_status(request):
    """
    Status bo'yicha foydalanuvchilarni qaytaradi
    """
    try:
        # PNFL bor foydalanuvchilar
        registered_users = Register.objects.filter(pnfl__isnull=False).values('telegram_id', 'pnfl', 'fio')
        
        # PNFL yo'q foydalanuvchilar
        incomplete_users = Register.objects.filter(pnfl__isnull=True).values('telegram_id', 'fio', 'username')
        
        return Response({
            'success': True,
            'data': {
                'registered_users': list(registered_users),
                'incomplete_users': list(incomplete_users),
                'registered_count': len(registered_users),
                'incomplete_count': len(incomplete_users)
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_user_by_telegram_id(request, telegram_id):
    """
    Telegram ID bo'yicha foydalanuvchining barcha ma'lumotlarini qaytaradi
    """
    try:
        user = Register.objects.filter(telegram_id=telegram_id).first()
        
        if not user:
            return Response({
                'success': False,
                'error': 'Foydalanuvchi topilmadi',
                'message': 'Bu telegram ID ga tegishli foydalanuvchi mavjud emas'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serializer orqali barcha ma'lumotlarni olish
        serializer = RegisterDetailSerializer(user)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Foydalanuvchi ma\'lumotlari muvaffaqiyatli olindi'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Ma\'lumotlarni olishda xatolik yuz berdi'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)