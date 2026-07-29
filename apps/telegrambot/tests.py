"""Tests for telegrambot app — vazifa yig'ish logikasi va login/link."""
from django.test import TestCase

from apps.courses.models import Course, CoursePurchase
from apps.exams.models import Test as ExamTest, Score
from apps.payments.models import Payment
from apps.school.models import Assignment, Subject
from apps.users.models import User

from .management.commands.runbot import _authenticate
from .models import TelegramLink
from .services import (
    build_admin_stats_message,
    build_todo_message,
    linked_users_text,
    pending_assignments_text,
    pending_tests_text,
)


class PendingAssignmentsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bot_student', password='pass1234')
        self.subject = Subject.objects.create(name='Matematika', icon='📐')

    def test_no_assignments_returns_none(self):
        self.assertIsNone(pending_assignments_text(self.user))

    def test_pending_assignment_shown(self):
        Assignment.objects.create(subject=self.subject, title='1-mavzu', status=Assignment.STATUS_PENDING)
        text = pending_assignments_text(self.user)
        self.assertIn('1-mavzu', text)
        self.assertIn('Matematika', text)

    def test_done_assignment_hidden(self):
        Assignment.objects.create(subject=self.subject, title='Bajarilgan', status=Assignment.STATUS_DONE)
        self.assertIsNone(pending_assignments_text(self.user))


class PendingTestsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bot_student2', password='pass1234')
        self.locked_course = Course.objects.create(
            slug='bot-backend', title_uz='Backend', type='IT',
            requires_purchase=True, price=400000,
        )

    def test_open_test_shown(self):
        ExamTest.objects.create(title='JS asoslari', type='IT', questions=[])
        text = pending_tests_text(self.user)
        self.assertIn('JS asoslari', text)

    def test_taken_test_hidden(self):
        test = ExamTest.objects.create(title='Topshirilgan', type='IT', questions=[])
        Score.objects.create(user=self.user, test=test, score=90)
        self.assertIsNone(pending_tests_text(self.user))

    def test_locked_course_test_hidden_without_purchase(self):
        ExamTest.objects.create(
            title='Backend testi', type='IT', questions=[], course=self.locked_course,
        )
        self.assertIsNone(pending_tests_text(self.user))

    def test_locked_course_test_shown_after_purchase(self):
        CoursePurchase.objects.create(user=self.user, course=self.locked_course)
        ExamTest.objects.create(
            title='Backend testi', type='IT', questions=[], course=self.locked_course,
        )
        text = pending_tests_text(self.user)
        self.assertIn('Backend testi', text)


class BuildTodoMessageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bot_student3', password='pass1234')

    def test_empty_state_message(self):
        text = build_todo_message(self.user)
        self.assertIn("Hozircha bajarilmagan vazifa yo'q", text)

    def test_combines_assignments_and_tests(self):
        subject = Subject.objects.create(name='Fizika')
        Assignment.objects.create(subject=subject, title='Vazifa', status=Assignment.STATUS_PENDING)
        ExamTest.objects.create(title='Test', type='School', questions=[])
        text = build_todo_message(self.user)
        self.assertIn('Maktab vazifalari', text)
        self.assertIn('Topshirilmagan testlar', text)


class TelegramLinkModelTests(TestCase):
    def test_link_created_and_unique(self):
        user = User.objects.create_user(username='linkuser', password='pass1234')
        link = TelegramLink.objects.create(telegram_id=123456, user=user)
        self.assertEqual(str(link), 'linkuser ↔ tg:123456')

        # Bir xil telegram_id ikkinchi marta ishlatib bo'lmaydi.
        other = User.objects.create_user(username='other', password='pass1234')
        with self.assertRaises(Exception):
            TelegramLink.objects.create(telegram_id=123456, user=other)


class AuthenticateHelperTests(TestCase):
    """Bot login qadamida ishlatiladigan _authenticate() funksiyasi."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='botauth', password='pass1234', full_name='Bot Auth',
        )

    def test_correct_credentials(self):
        user, error = _authenticate('botauth', 'pass1234')
        self.assertIsNone(error)
        self.assertEqual(user.username, 'botauth')

    def test_wrong_password(self):
        user, error = _authenticate('botauth', 'notpass')
        self.assertIsNone(user)
        self.assertIn("noto'g'ri", error)

    def test_unknown_username(self):
        user, error = _authenticate('yoq_user', 'pass1234')
        self.assertIsNone(user)
        self.assertIn('topilmadi', error)

    def test_blocked_user(self):
        self.user.is_blocked = True
        self.user.save()
        user, error = _authenticate('botauth', 'pass1234')
        self.assertIsNone(user)
        self.assertIn('bloklangan', error)


class AdminStatsTests(TestCase):
    """Bot admin statistikasi — botga ulanganlar, to'lovlar, obunalar soni."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='bot_admin', password='pass1234', role=User.ROLE_ADMIN, is_staff=True,
        )
        self.student1 = User.objects.create_user(
            username='bot_s1', password='pass1234', plan=User.PLAN_STUDENT,
        )
        self.student2 = User.objects.create_user(username='bot_s2', password='pass1234')
        self.teacher = User.objects.create_user(
            username='bot_t1', password='pass1234', role=User.ROLE_TEACHER,
        )

    def test_stats_counts_users_by_role(self):
        text = build_admin_stats_message()
        self.assertIn('👥 Jami foydalanuvchilar: *4*', text)
        self.assertIn('O\'quvchi: 2', text)
        self.assertIn('O\'qituvchi: 1', text)
        self.assertIn('Admin: 1', text)

    def test_stats_counts_linked_bot_users(self):
        TelegramLink.objects.create(telegram_id=111, user=self.student1)
        TelegramLink.objects.create(telegram_id=222, user=self.student2)
        text = build_admin_stats_message()
        self.assertIn('Botga ulangan (login qilgan): *2*', text)

    def test_stats_counts_pending_payments(self):
        Payment.objects.create(user=self.student1, kind=Payment.KIND_SUBSCRIPTION,
                                plan='student', duration='week', amount=9000)
        Payment.objects.create(user=self.student2, kind=Payment.KIND_SUBSCRIPTION,
                                plan='student', duration='week', amount=9000,
                                status=Payment.STATUS_CONFIRMED)
        text = build_admin_stats_message()
        self.assertIn('Kutilmoqda: 1', text)
        self.assertIn('Tasdiqlangan: 1', text)

    def test_stats_counts_active_subscriptions(self):
        text = build_admin_stats_message()
        self.assertIn('Faol obunalar: 1', text)  # faqat student1 plan=student


class LinkedUsersTextTests(TestCase):
    def test_no_links_message(self):
        text = linked_users_text()
        self.assertIn("hech kim botga ulanmagan", text)

    def test_lists_linked_users(self):
        user = User.objects.create_user(
            username='bot_linked', password='pass1234', full_name='Linked User',
        )
        TelegramLink.objects.create(telegram_id=555, user=user)
        text = linked_users_text()
        self.assertIn('Linked User', text)
        self.assertIn('@bot_linked', text)
