"""Serializers for payments app."""
from rest_framework import serializers

from apps.courses.models import Course

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """To'lov.

    `user` va `plan_name` — admin ro'yxatida kim va qaysi tarifga to'lov
    qilganini ko'rsatish uchun (foydalanuvchining o'z tarixida ortiqcha,
    lekin zarar emas — bitta serializer ikkala view uchun ham yetarli).
    """
    user = serializers.SerializerMethodField()
    plan_name = serializers.CharField(source='get_plan_display', read_only=True)
    course_title = serializers.CharField(source='course.title_uz', read_only=True, default=None)

    class Meta:
        model = Payment
        fields = ('id', 'user', 'kind', 'plan', 'plan_name', 'course', 'course_title',
                   'amount', 'screenshot', 'status', 'admin_note', 'created_at')
        read_only_fields = ('id', 'status', 'admin_note', 'created_at')

    def get_user(self, obj):
        return {
            'id': obj.user_id,
            'username': obj.user.username,
            'full_name': obj.user.full_name,
        }


class PaymentSubmitSerializer(serializers.Serializer):
    """To'lov yuborish — admin tasdiqlashi kerak.

    `kind=subscription` — `plan` (student/premium) talab qilinadi, summa
    `Payment.PLAN_PRICES` bilan solishtiriladi.
    `kind=course` — `course` (kurs id) talab qilinadi, summa shu
    kursning `price`'i bilan solishtiriladi.
    """
    kind = serializers.ChoiceField(choices=[k[0] for k in Payment.KIND_CHOICES], default=Payment.KIND_SUBSCRIPTION)
    plan = serializers.ChoiceField(
        choices=[p[0] for p in Payment.PLAN_CHOICES if p[0] != 'free'], required=False,
    )
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=False)
    amount = serializers.IntegerField(min_value=0)
    screenshot = serializers.ImageField(required=False, allow_null=True)

    def validate(self, attrs):
        kind = attrs.get('kind', Payment.KIND_SUBSCRIPTION)
        amount = attrs.get('amount', 0)

        if kind == Payment.KIND_SUBSCRIPTION:
            plan = attrs.get('plan')
            if not plan:
                raise serializers.ValidationError({'plan': "Tarif tanlanishi kerak"})
            expected = Payment.PLAN_PRICES.get(plan, 0)
            if expected and amount != expected:
                raise serializers.ValidationError(
                    {'amount': f"{plan} tarif uchun {expected} so'm to'g'ri keladi"}
                )
        else:  # kind == KIND_COURSE
            course = attrs.get('course')
            if not course:
                raise serializers.ValidationError({'course': "Kurs tanlanishi kerak"})
            if not course.requires_purchase:
                raise serializers.ValidationError({'course': "Bu kurs sotib olinmaydi"})
            if course.price and amount != course.price:
                raise serializers.ValidationError(
                    {'amount': f"{course.title_uz} uchun {course.price} so'm to'g'ri keladi"}
                )

        return attrs


class AdminActionSerializer(serializers.Serializer):
    """Admin — to'lovni tasdiqlash/rad etish."""
    action = serializers.ChoiceField(choices=['confirm', 'reject'])
    note = serializers.CharField(required=False, allow_blank=True, default='')