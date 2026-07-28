"""Bot uchun ma'lumot yig'ish — handler'lardan ajratilgan (test qilish oson bo'lsin uchun)."""
from apps.courses.models import CoursePurchase
from apps.exams.models import Test as ExamTest
from apps.school.models import Assignment


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
