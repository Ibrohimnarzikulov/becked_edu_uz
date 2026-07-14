"""Serializers for users app."""
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    """Ro'yxatdan o'tish — yangi foydalanuvchi (role=student)."""
    password = serializers.CharField(write_only=True, min_length=4, validators=[validate_password])
    bio = serializers.CharField(required=False, allow_blank=True, default='')
    track = serializers.CharField(required=False, allow_blank=True, default='')
    grade = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ('username', 'password', 'full_name', 'bio', 'track', 'grade')

    def validate_username(self, value):
        value = value.lower().strip()
        if len(value) < 3:
            raise serializers.ValidationError("Username kamida 3 ta belgi bo'lishi kerak")
        if ' ' in value:
            raise serializers.ValidationError("Username bo'sh joy qabul qilmaydi")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username band")
        return value

    def validate_full_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Ism va familiyani kiriting")
        return value.strip()

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(role=User.ROLE_STUDENT, **validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Login — JWT token qaytaradi."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs['username'].lower().strip()
        password = attrs['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "Login yoki parol noto'g'ri"})

        if user.is_blocked:
            raise serializers.ValidationError({"error": "BLOCKED"})

        if not user.check_password(password):
            raise serializers.ValidationError({"error": "Login yoki parol noto'g'ri"})

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Profil — GET/PATCH."""
    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'bio', 'track', 'grade',
            'role', 'plan', 'is_blocked', 'date_joined',
        )
        read_only_fields = ('id', 'username', 'role', 'plan', 'is_blocked', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    """Parol o'zgartirish."""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto'g'ri")
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    """Admin — barcha foydalanuvchilar."""
    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'role', 'plan',
            'track', 'grade', 'is_blocked', 'date_joined',
        )
        read_only_fields = fields


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """Admin — yangi foydalanuvchi (o'qituvchi/admin/o'quvchi) yaratadi."""
    password = serializers.CharField(write_only=True, min_length=4, validators=[validate_password])
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default=User.ROLE_TEACHER)

    class Meta:
        model = User
        fields = ('username', 'password', 'full_name', 'role', 'track', 'grade')

    def validate_username(self, value):
        value = value.lower().strip()
        if len(value) < 3:
            raise serializers.ValidationError("Username kamida 3 ta belgi bo'lishi kerak")
        if ' ' in value:
            raise serializers.ValidationError("Username bo'sh joy qabul qilmaydi")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username band")
        return value

    def validate_full_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Ism va familiyani kiriting")
        return value.strip()

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', User.ROLE_TEACHER)
        user = User(**validated_data)
        user.set_password(password)
        # Admin rolidagi user Django admin panelga ham kira olsin
        if role == User.ROLE_ADMIN:
            user.is_staff = True
        user.save()
        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Admin — user roli va/yoki planini o'zgartirish.

    Faqat `role` va `plan` maydonlarini qabul qiladi. Boshqa maydonlar
    o'qib bo'lmaydi (read-only) — bu orqali admin username/email va h.k.
    ni tasodifan o'zgartirib yubormasligi ta'minlanadi.
    """
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    plan = serializers.ChoiceField(choices=User.PLAN_CHOICES, required=False)

    class Meta:
        model = User
        fields = ('role', 'plan')

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Kamida bitta maydon yuborilishi kerak")
        return attrs


def get_tokens_for_user(user):
    """JWT access va refresh tokenlar."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
