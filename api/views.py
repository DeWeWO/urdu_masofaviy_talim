from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import TelegramGroup, Register
from .serializers import TelegramGroupSerializers, RegisterSerializer

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
    queryset = Register.objects.all()
    serializer_class = RegisterSerializer