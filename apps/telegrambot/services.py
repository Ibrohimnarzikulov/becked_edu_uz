"""Bot uchun ma'lumot yig'ish — handler'lardan ajratilgan (test qilish oson bo'lsin uchun)."""
from django.contrib.auth import get_user_model

from apps.courses.models import CoursePurchase
from apps.exams.models import Test as ExamTest
from apps.payments.models import Payment
from apps.school.models import Assignment

from .models import TelegramLink

User = get_user_model()


def pending_assignments_text(user):
    """Bajarilmagan maktab vazifalari (hozircha global — Assignment userga bog'lanmagan)."""
    items = list(
        Assignment.objects
        .exclude(status__in=[Assignment.STATUS_DONE, Assignment.STATUS_SUBMITTED])
        .select_related('subject')[:20]
    )
    if not items:
        return None
    lines = [
        f"• {a.subject.icon} {a.subject.name} — {a.title} ({a.get_status_display()})"
        for a in items
    ]
    return "\n".join(lines)


def pending_tests_text(user):
    """Foydalanuvchi hali topshirmagan testlar — sotib olinmagan kurs testlari chiqarib tashlanadi."""
    purchased_ids = set(
        CoursePurchase.objects.filter(user=user).values_list('course_id', flat=True)
    )
    taken_ids = set(
        ExamTest.objects.filter(scores__user=user).values_list('id', flat=True)
    )
    qs = ExamTest.objects.exclude(id__in=taken_ids).select_related('course')[:50]

    lines = []
    for t in qs:
        if t.course_id and t.course.requires_purchase and t.course_id not in purchased_ids:
            continue  # sotib olinmagan kurs testi — bot ko'rsatmaydi
        lines.append(f"• 📝 {t.title} ({t.get_type_display()})")
        if len(lines) >= 20:
            break
    return "\n".join(lines) if lines else None


def build_todo_message(user):
    """Bot /vazifalar javobida yuboriladigan matn."""
    assignments = pending_assignments_text(user)
    tests = pending_tests_text(user)

    if not assignments and not tests:
        return "🎉 Hozircha bajarilmagan vazifa yo'q!"

    parts = []
    if assignments:
        parts.append("📚 *Maktab vazifalari:*\n" + assignments)
    if tests:
        parts.append("📝 *Topshirilmagan testlar:*\n" + tests)
    return "\n\n".join(parts)


def build_admin_stats_message():
    """Faqat admin uchun — bot va sayt bo'yicha umumiy statistika."""
    total_users = User.objects.count()
    students = User.objects.filter(role=User.ROLE_STUDENT).count()
    teachers = User.objects.filter(role=User.ROLE_TEACHER).count()
    admins = User.objects.filter(role=User.ROLE_ADMIN).count()
    blocked = User.objects.filter(is_blocked=True).count()

    linked = TelegramLink.objects.count()

    pending_payments = Payment.objects.filter(status=Payment.STATUS_PENDING).count()
    confirmed_payments = Payment.objects.filter(status=Payment.STATUS_CONFIRMED).count()

    active_subs = User.objects.filter(plan=User.PLAN_STUDENT).count()
    course_purchases = CoursePurchase.objects.count()

    return (
        "📊 *EduHub statistikasi*\n\n"
        f"👥 Jami foydalanuvchilar: *{total_users}*\n"
        f"   • O'quvchi: {students}\n"
        f"   • O'qituvchi: {teachers}\n"
        f"   • Admin: {admins}\n"
        f"   • Bloklangan: {blocked}\n\n"
        f"🤖 Botga ulangan (login qilgan): *{linked}*\n\n"
        f"💳 To'lovlar:\n"
        f"   • Kutilmoqda: {pending_payments}\n"
        f"   • Tasdiqlangan: {confirmed_payments}\n\n"
        f"🎓 Faol obunalar: {active_subs}\n"
        f"📦 Sotib olingan kurslar: {course_purchases}"
    )


def linked_users_text():
    """Botga ulangan foydalanuvchilar ro'yxati (admin uchun)."""
    links = TelegramLink.objects.select_related('user').order_by('-linked_at')[:30]
    if not links:
        return "Hozircha hech kim botga ulanmagan."
    lines = [
        f"• {l.user.full_name or l.user.username} (@{l.user.username}) — {l.linked_at.strftime('%Y-%m-%d %H:%M')}"
        for l in links
    ]
    return "🔗 *Botga ulangan foydalanuvchilar:*\n\n" + "\n".join(lines)
