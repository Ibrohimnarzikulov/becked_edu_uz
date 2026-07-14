"""Serializers for payments app."""
from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """To'lov — foydalanuvchiga."""
    class Meta:
        model = Payment
        fields = ('id', 'plan', 'amount', 'screenshot', 'status', 'admin_note', 'created_at')
        read_only_fields = ('id', 'status', 'admin_note', 'created_at')


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