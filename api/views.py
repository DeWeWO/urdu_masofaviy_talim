from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import TelegramGroup
from .serializers import TelegramGroupSerializers

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

