"""Serializers for payments app."""
from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """To'lov.

    `user` va `plan_name` — admin ro'yxatida kim va qaysi tarifga to'lov
    qilganini ko'rsatish uchun (foydalanuvchining o'z tarixida ortiqcha,
    lekin zarar emas — bitta serializer ikkala view uchun ham yetarli).
    """
    user = serializers.SerializerMethodField()
    plan_name = serializers.CharField(source='get_plan_display', read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'user', 'plan', 'plan_name', 'amount', 'screenshot',
                   'status', 'admin_note', 'created_at')
        read_only_fields = ('id', 'status', 'admin_note', 'created_at')

    def get_user(self, obj):
        return {
            'id': obj.user_id,
            'username': obj.user.username,
            'full_name': obj.user.full_name,
        }


class PaymentSubmitSerializer(serializers.Serializer):
    """To'lov yuborish — admin tasdiqlashi kerak."""
    plan = serializers.ChoiceField(choices=[p[0] for p in Payment.PLAN_CHOICES if p[0] != 'free'])
    amount = serializers.IntegerField(min_value=0)
    screenshot = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        plan = attrs.get('plan')
        amount = attrs.get('amount', 0)
        expected = Payment.PLAN_PRICES.get(plan, 0)
        if expected and amount != expected:
            raise serializers.ValidationError(
                {'amount': f"{plan} tarif uchun {expected} so'm to'g'ri keladi"}
            )
        return attrs


class AdminActionSerializer(serializers.Serializer):
    """Admin — to'lovni tasdiqlash/rad etish."""
    action = serializers.ChoiceField(choices=['confirm', 'reject'])
    note = serializers.CharField(required=False, allow_blank=True, default='')