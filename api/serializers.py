from rest_framework import serializers
from core.models import TelegramGroup

class TelegramGroupSerializers(serializers.ModelSerializer):
    class Meta:
        model = TelegramGroup
        fields = ['group_name', 'group_id']
        
    def create(self, validated_data):
        group, created = TelegramGroup.objects.get_or_create(
            group_id=validated_data['group_id'],
            defaults={'group_name': validated_data['group_name']}
        )
        if not created:
            group.group_name = validated_data['group_name']
            group.is_active = True
            group.save()
        return group