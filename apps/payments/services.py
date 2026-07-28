"""To'lovni tasdiqlash bo'yicha umumiy mantiq.

`AdminPaymentActionView` (API) va Django admin bulk action ikkalasi ham
shu funksiyani chaqiradi — mantiq bir joyda, ikki marta yozilmaydi.
"""
from datetime import timedelta

from django.utils import timezone

from apps.courses.models import CoursePurchase

from .models import Payment


def apply_confirmed_payment(payment):
    """`payment.status` allaqachon CONFIRMED qilib qo'yilgan deb hisoblanadi.

    kind=course — CoursePurchase yaratadi (muddatsiz).
    kind=subscription — user.plan='student' qiladi va muddatni
    plan_expires_at'ga qo'shadi (agar hali eski obuna tugamagan bo'lsa,
    yangi muddat ustiga qo'shiladi — uzaytirish).
    """
    if payment.kind == Payment.KIND_COURSE:
        if payment.course_id:
            CoursePurchase.objects.get_or_create(user=payment.user, course_id=payment.course_id)
        return

    user = payment.user
    days = Payment.DURATION_DAYS.get(payment.duration, 30)
    now = timezone.now()
    base = user.plan_expires_at if (user.plan_expires_at and user.plan_expires_at > now) else now
    user.plan = Payment.PLAN_STUDENT
    user.plan_expires_at = base + timedelta(days=days)
    user.save(update_fields=['plan', 'plan_expires_at'])
