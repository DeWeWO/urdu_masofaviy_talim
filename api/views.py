from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import TelegramGroup, Register, MemberActivity
from .serializers import (
    TelegramGroupSerializer, RegisterSerializer, RegisterStatusSerializer,
    MemberActivityCreateSerializer, MemberActivityListSerializer
    )

import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def add_telegram_group(request):
    serializer = TelegramGroupSerializer(data=request.data)
    if serializer.is_valid():
        group = serializer.save()
        return Response({
            'success': True,
            'message': 'Group added successfully',
            'group_id': group.group_id,
            'group_name': group.group_name
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

class RegisterListCreateView(generics.ListCreateAPIView):
    queryset = Register.objects.select_related('hemis_data').prefetch_related('register_groups')
    serializer_class = RegisterSerializer

class RegisterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RegisterSerializer
    lookup_field = 'telegram_id'
    
    def get_queryset(self):
        return Register.objects.select_related('hemis_data').prefetch_related('register_groups')


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
            # RegisterStatusSerializer dan foydalanish
            serializer = RegisterStatusSerializer(user)
            
            return Response({
                'success': True,
                'status': 'registered',
                'message': 'Foydalanuvchi ro\'yxatdan o\'tgan',
                'action': 'update_info',
                'user_data': serializer.data
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
        registered_users = Register.objects.filter(
            pnfl__isnull=False
        ).exclude(pnfl='').values('telegram_id', 'pnfl', 'fio')
        
        # PNFL yo'q foydalanuvchilar
        incomplete_users = Register.objects.filter(
            pnfl__isnull=True
        ).values('telegram_id', 'fio', 'username')
        
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
        user = Register.objects.select_related('hemis_data').prefetch_related(
            'register_groups'
        ).filter(telegram_id=telegram_id).first()
        
        if not user:
            return Response({
                'success': False,
                'error': 'Foydalanuvchi topilmadi',
                'message': 'Bu telegram ID ga tegishli foydalanuvchi mavjud emas'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # RegisterSerializer dan foydalanish
        serializer = RegisterSerializer(user)
        
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

class MemberActivityCreateView(generics.CreateAPIView):
    """A'zo faoliyatini yaratish API"""
    queryset = MemberActivity.objects.all()
    serializer_class = MemberActivityCreateSerializer
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                instance = serializer.save()
                logger.info(f"Member activity created: {instance}")
                return Response({
                    "success": True,
                    "message": "A'zo faoliyati muvaffaqiyatli yaratildi",
                    "data": {
                        "id": instance.id,
                        "activity_type": instance.activity_type,
                        "user": instance.user_display_name,
                        "group": instance.telegram_group.group_name
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Member activity validation error: {serializer.errors}")
                return Response({
                    "success": False,
                    "message": "Validation xatolik",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Member activity creation error: {e}")
            return Response({
                "success": False,
                "message": f"Server xatolik: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MemberActivityListView(generics.ListAPIView):
    """A'zo faoliyatlari ro'yxati API"""
    serializer_class = MemberActivityListSerializer
    
    def get_queryset(self):
        queryset = MemberActivity.objects.select_related('register', 'telegram_group').all()
        
        # Filter parametrlari
        telegram_id = self.request.query_params.get('telegram_id')
        group_id = self.request.query_params.get('group_id')
        activity_type = self.request.query_params.get('activity_type')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if telegram_id:
            queryset = queryset.filter(register__telegram_id=telegram_id)
        if group_id:
            queryset = queryset.filter(telegram_group__group_id=group_id)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(activity_time__gte=date_from)
            except ValueError:
                pass
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(activity_time__lte=date_to)
            except ValueError:
                pass
        
        return queryset


@api_view(['GET'])
def member_activity_stats(request):
    """A'zo faoliyatlari statistikasi"""
    try:
        from django.db.models import Count, Q
        
        # Umumiy statistika
        total_activities = MemberActivity.objects.count()
        join_count = MemberActivity.objects.filter(activity_type='join').count()
        leave_count = MemberActivity.objects.filter(activity_type__in=['leave', 'kicked', 'removed']).count()
        
        # Guruh bo'yicha statistika
        group_stats = MemberActivity.objects.values('telegram_group__group_name').annotate(
            total=Count('id'),
            joins=Count('id', filter=Q(activity_type='join')),
            leaves=Count('id', filter=Q(activity_type__in=['leave', 'kicked', 'removed']))
        )
        
        return Response({
            "success": True,
            "data": {
                "total_activities": total_activities,
                "join_count": join_count,
                "leave_count": leave_count,
                "group_stats": list(group_stats)
            }
        })
    
    except Exception as e:
        logger.exception(f"Stats error: {e}")
        return Response({
            "success": False,
            "message": f"Statistika xatolik: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)