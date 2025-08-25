from rest_framework import serializers
from core.models import TelegramGroup, Register

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

class RegisterSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Register
        fields = [
            'id', 'telegram_id', 'username', 'fio',
            'group_id', 'register_group', 'pnfl', 'tg_tel',
            'tel', 'parent_tel', 'address', 'is_active', 'is_teacher',
            'created', 'updated'
        ]
        read_only_fields = ['register_group', 'created', 'updated']

    def create(self, validated_data):
        group_id = validated_data.pop("group_id", None)
        if "is_active" not in validated_data:
            validated_data["is_active"] = False
        if group_id:
            try:
                tg_group = TelegramGroup.objects.get(group_id=group_id)
            except TelegramGroup.DoesNotExist:
                raise serializers.ValidationError({"group_id": "Bunday Telegram group mavjud emas"})
            validated_data["register_group"] = tg_group
        return super().create(validated_data)
