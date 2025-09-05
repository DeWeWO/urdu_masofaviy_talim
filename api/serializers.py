from rest_framework import serializers
from core.models import TelegramGroup, Register, HemisTable


class TelegramGroupSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TelegramGroup
        fields = ['id', 'group_name', 'group_id', 'is_active', 'members_count', 'created']
        extra_kwargs = {
            'group_id': {'validators': []},  # unique validatorni olib tashlash
        }
        
    def get_members_count(self, obj):
        return obj.members.filter(is_active=True).count()
    
    def create(self, validated_data):
        group, created = TelegramGroup.objects.get_or_create(
            group_id=validated_data['group_id'],
            defaults={
                'group_name': validated_data.get('group_name'),
                'is_active': True
            }
        )
        if not created:
            # Mavjud guruhni yangilash
            group.group_name = validated_data.get('group_name', group.group_name)
            group.is_active = True
            group.save(update_fields=['group_name', 'is_active', 'updated'])
        return group


class RegisterSerializer(serializers.ModelSerializer):
    group_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False,
        allow_empty=True
    )
    register_groups = serializers.SerializerMethodField(read_only=True)
    hemis_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Register
        fields = [
            'id', 'telegram_id', 'username', 'fio',
            'group_ids', 'register_groups', 'hemis_data',
            'hemis_id', 'pnfl', 'tg_tel', 'tel', 'parent_tel', 
            'address', 'is_active', 'is_teacher',
            'created', 'updated'
        ]
        extra_kwargs = {
            'telegram_id': {'validators': []},  # unique validatorni olib tashlash
            'hemis_id': {'validators': []},
            'pnfl': {'validators': []},
            'created': {'read_only': True},
            'updated': {'read_only': True},
        }

    def get_register_groups(self, obj):
        return [
            {
                'id': group.id,
                'group_name': group.group_name,
                'group_id': group.group_id,
                'is_active': group.is_active
            }
            for group in obj.register_groups.all()
        ]
    
    def get_hemis_data(self, obj):
        if hasattr(obj, 'hemis_data') and obj.hemis_data:
            return {
                'fio': obj.hemis_data.fio,
                'course': obj.hemis_data.course,
                'student_group': obj.hemis_data.student_group,
                'passport': obj.hemis_data.passport,
                'born': obj.hemis_data.born
            }
        return None

    def validate_pnfl(self, value):
        if value and len(str(value)) != 14:
            raise serializers.ValidationError("PNFL 14 ta raqam bo'lishi kerak")
        return value

    def validate_group_ids(self, value):
        if value:
            existing_groups = TelegramGroup.objects.filter(
                group_id__in=value
            ).values_list('group_id', flat=True)
            
            missing_groups = set(value) - set(existing_groups)
            if missing_groups:
                raise serializers.ValidationError(
                    f"Bu guruhlar topilmadi: {list(missing_groups)}"
                )
        return value

    def create(self, validated_data):
        group_ids = validated_data.pop("group_ids", [])
        
        # get_or_create ishlatish
        register, created = Register.objects.get_or_create(
            telegram_id=validated_data['telegram_id'],
            defaults=validated_data
        )
        
        if not created:
            # Mavjud registerni yangilash
            for attr, value in validated_data.items():
                setattr(register, attr, value)
            register.save()

        # Guruhlarni bog'lash
        if group_ids:
            groups = TelegramGroup.objects.filter(group_id__in=group_ids)
            register.register_groups.set(groups)
        
        return register

    def update(self, instance, validated_data):
        group_ids = validated_data.pop("group_ids", None)
        
        # Asosiy maydonlarni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Guruhlarni yangilash
        if group_ids is not None:
            groups = TelegramGroup.objects.filter(group_id__in=group_ids)
            instance.register_groups.set(groups)
        
        return instance


class RegisterCreateSerializer(serializers.ModelSerializer):
    """Yangi register yaratish uchun minimal serializer"""
    
    class Meta:
        model = Register
        fields = ['telegram_id', 'username', 'fio']
        extra_kwargs = {
            'telegram_id': {'validators': []},
        }
    
    def create(self, validated_data):
        register, created = Register.objects.get_or_create(
            telegram_id=validated_data['telegram_id'],
            defaults=validated_data
        )
        return register


class RegisterStatusSerializer(serializers.ModelSerializer):
    """Status tekshirish uchun"""
    has_hemis_data = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Register
        fields = [
            'telegram_id', 'username', 'fio', 'pnfl', 
            'hemis_id', 'is_active', 'is_teacher',
            'has_hemis_data', 'groups_count'
        ]
    
    def get_has_hemis_data(self, obj):
        return hasattr(obj, 'hemis_data') and obj.hemis_data is not None
    
    def get_groups_count(self, obj):
        return obj.register_groups.filter(is_active=True).count()


class HemisTableSerializer(serializers.ModelSerializer):
    """HemisTable uchun serializer"""
    register_info = serializers.SerializerMethodField()
    telegram_groups = serializers.SerializerMethodField()
    
    class Meta:
        model = HemisTable
        fields = [
            'id', 'hemis_id', 'fio', 'born', 'passport', 'pnfl',
            'course', 'student_group', 'register_info', 'telegram_groups',
            'created', 'updated'
        ]
        extra_kwargs = {
            'hemis_id': {'validators': []},
            'pnfl': {'validators': []},
            'passport': {'validators': []},
        }
    
    def get_register_info(self, obj):
        if obj.register:
            return {
                'telegram_id': obj.register.telegram_id,
                'username': obj.register.username,
                'is_active': obj.register.is_active
            }
        return None
    
    def get_telegram_groups(self, obj):
        return [
            {
                'id': group.id,
                'group_name': group.group_name,
                'group_id': group.group_id
            }
            for group in obj.telegram_groups.filter(is_active=True)
        ]


class BulkRegisterSerializer(serializers.Serializer):
    """Ko'p registerni bir vaqtda yaratish uchun"""
    registers = RegisterCreateSerializer(many=True)
    
    def create(self, validated_data):
        registers_data = validated_data['registers']
        created_registers = []
        
        for register_data in registers_data:
            register, created = Register.objects.get_or_create(
                telegram_id=register_data['telegram_id'],
                defaults=register_data
            )
            if created:
                created_registers.append(register)
        
        return {'created_count': len(created_registers), 'registers': created_registers}


# Statistika uchun serializer
class StatisticsSerializer(serializers.Serializer):
    total_registers = serializers.IntegerField()
    active_registers = serializers.IntegerField()
    total_groups = serializers.IntegerField()
    active_groups = serializers.IntegerField()
    total_hemis_records = serializers.IntegerField()
    linked_records = serializers.IntegerField()
    completion_rate = serializers.FloatField()