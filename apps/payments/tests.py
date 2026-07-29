"""Tests for payments app."""
from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.courses.models import Course, CoursePurchase
from apps.users.models import User
from .admin import PaymentAdmin
from .models import Payment


class PaymentTests(TestCase):
    """To'lov testlari."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='student', password='test1234', plan=User.PLAN_FREE,
        )
        self.admin = User.objects.create_user(
            username='admin', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )

    def test_submit_payment_success(self):
        """To'lov so'rovini yuborish (1 hafta muddat)."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'kind': 'subscription', 'duration': 'week', 'amount': 9000},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.first()
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.duration, 'week')
        self.assertEqual(payment.plan, 'student')  # barcha muddatlar shu tarifni ochadi

    def test_submit_payment_wrong_amount(self):
        """Noto'g'ri summa bilan yuborish — xato."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'kind': 'subscription', 'duration': 'week', 'amount': 5000},  # 9000 bo'lishi kerak
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_submit_payment_missing_duration(self):
        """Muddat tanlanmasa — xato."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'kind': 'subscription', 'amount': 9000},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_my_payments_list(self):
        """Foydalanuvchi o'z to'lovlarini ko'radi."""
        Payment.objects.create(user=self.user, plan='student', amount=75000)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('my-payments'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_admin_list_payments(self):
        """Admin barcha to'lovlarni ko'radi — kim to'laganini bilishi kerak."""
        Payment.objects.create(user=self.user, plan='student', amount=75000)
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-payments'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['username'], 'student')
        self.assertEqual(response.data[0]['plan_name'], 'Student')

    def test_student_cannot_list_admin_payments(self):
        """Student admin to'lovlarini ko'ra olmaydi."""
        Payment.objects.create(user=self.user, plan='student', amount=75000)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('admin-payments'))
        self.assertEqual(response.status_code, 403)

    def test_admin_confirm_payment(self):
        """Admin to'lovni tasdiqlaydi va plan yangilanadi."""
        payment = Payment.objects.create(
            user=self.user, plan='student', amount=75000,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-payment-action', kwargs={'payment_id': payment.id}),
            {'action': 'confirm', 'note': 'OK'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_CONFIRMED)
        self.assertEqual(self.user.plan, User.PLAN_STUDENT)

    def test_admin_reject_payment(self):
        """Admin to'lovni rad etadi — plan o'zgarmaydi."""
        payment = Payment.objects.create(
            user=self.user, plan='premium', amount=150000,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-payment-action', kwargs={'payment_id': payment.id}),
            {'action': 'reject', 'note': 'Chek ko\'rinmaydi'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_REJECTED)
        self.assertEqual(self.user.plan, User.PLAN_FREE)  # eski plani

    def test_cannot_action_confirmed_payment(self):
        """Allaqachon tasdiqlangan to'lovni qayta tasdiqlab bo'lmaydi."""
        payment = Payment.objects.create(
            user=self.user, plan='student', amount=75000,
            status=Payment.STATUS_CONFIRMED,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-payment-action', kwargs={'payment_id': payment.id}),
            {'action': 'confirm'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)


class CoursePaymentTests(TestCase):
    """Kurs sotib olish to'lovi — obunadan mustaqil, alohida oqim."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='coursebuyer', password='test1234', plan=User.PLAN_FREE,
        )
        self.admin = User.objects.create_user(
            username='payadmin', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )
        self.course = Course.objects.create(
            slug='backend3', title_uz='Backend', type='IT',
            requires_purchase=True, price=400000,
        )

    def test_submit_course_payment_success(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'kind': 'course', 'course': self.course.id, 'amount': 400000},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        payment = Payment.objects.first()
        self.assertEqual(payment.kind, Payment.KIND_COURSE)
        self.assertEqual(payment.course_id, self.course.id)

    def test_submit_course_payment_wrong_amount(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'kind': 'course', 'course': self.course.id, 'amount': 100000},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_submit_course_payment_requires_course(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'kind': 'course', 'amount': 400000},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_buy_non_purchasable_course(self):
        """requires_purchase=False kursni sotib olib bo'lmaydi."""
        free_course = Course.objects.create(slug='free-course', title_uz='Bepul', type='IT')
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'kind': 'course', 'course': free_course.id, 'amount': 0},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_confirm_course_payment_creates_purchase(self):
        """Admin tasdiqlaganda CoursePurchase yaratiladi, plan o'zgarmaydi."""
        payment = Payment.objects.create(
            user=self.user, kind=Payment.KIND_COURSE, course=self.course, amount=400000,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-payment-action', kwargs={'payment_id': payment.id}),
            {'action': 'confirm'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            CoursePurchase.objects.filter(user=self.user, course=self.course).exists()
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.plan, User.PLAN_FREE)  # obuna o'zgarmadi

    def test_course_payment_in_admin_list_shows_course_title(self):
        Payment.objects.create(
            user=self.user, kind=Payment.KIND_COURSE, course=self.course, amount=400000,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-payments'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['course_title'], 'Backend')


class SubscriptionDurationTests(TestCase):
    """Hafta/oy/yil obuna — muddat tugashi bilan."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='durationbuyer', password='test1234', plan=User.PLAN_FREE,
        )
        self.admin = User.objects.create_user(
            username='durationadmin', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )

    def test_confirm_sets_plan_and_expiry(self):
        payment = Payment.objects.create(
            user=self.user, kind=Payment.KIND_SUBSCRIPTION,
            plan='student', duration='week', amount=9000,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-payment-action', kwargs={'payment_id': payment.id}),
            {'action': 'confirm'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.plan, User.PLAN_STUDENT)
        self.assertIsNotNone(self.user.plan_expires_at)
        expected = timezone.now() + timedelta(days=7)
        self.assertAlmostEqual(
            self.user.plan_expires_at.timestamp(), expected.timestamp(), delta=10,
        )

    def test_confirm_extends_existing_active_subscription(self):
        """Muddati tugamagan obunaga yangi to'lov — mavjud muddat ustiga qo'shiladi."""
        future = timezone.now() + timedelta(days=5)
        self.user.plan = User.PLAN_STUDENT
        self.user.plan_expires_at = future
        self.user.save()

        payment = Payment.objects.create(
            user=self.user, kind=Payment.KIND_SUBSCRIPTION,
            plan='student', duration='week', amount=9000,  # +7 kun
        )
        self.client.force_authenticate(self.admin)
        self.client.post(
            reverse('admin-payment-action', kwargs={'payment_id': payment.id}),
            {'action': 'confirm'}, format='json',
        )
        self.user.refresh_from_db()
        expected = future + timedelta(days=7)
        self.assertAlmostEqual(
            self.user.plan_expires_at.timestamp(), expected.timestamp(), delta=10,
        )

    def test_sync_plan_expiry_downgrades_expired_user(self):
        self.user.plan = User.PLAN_STUDENT
        self.user.plan_expires_at = timezone.now() - timedelta(days=1)
        self.user.save()

        self.user.sync_plan_expiry()

        self.assertEqual(self.user.plan, User.PLAN_FREE)
        self.assertIsNone(self.user.plan_expires_at)

    def test_sync_plan_expiry_keeps_active_user(self):
        future = timezone.now() + timedelta(days=3)
        self.user.plan = User.PLAN_STUDENT
        self.user.plan_expires_at = future
        self.user.save()

        self.user.sync_plan_expiry()

        self.assertEqual(self.user.plan, User.PLAN_STUDENT)
        self.assertEqual(self.user.plan_expires_at, future)

    def test_daily_limit_reflects_expiry(self):
        """Muddati o'tgan foydalanuvchi kunlik-limit endpointida free bo'lib qoladi."""
        self.user.plan = User.PLAN_STUDENT
        self.user.plan_expires_at = timezone.now() - timedelta(days=1)
        self.user.save()

        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('daily-limit'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['plan'], 'free')
        self.assertEqual(response.data['limit'], 3)


class PaymentAdminDirectEditTests(TestCase):
    """Production'da haqiqiy bug: admin Payment forma ichida `status`ni
    to'g'ridan-to'g'ri "Tasdiqlandi" qilib saqlasa (bulk "Tasdiqlash"
    action'dan foydalanmasdan), CoursePurchase/obuna baribir yaratilishi
    kerak. Avval save_model() override qilinmagani uchun bu holatda
    hech narsa yaratilmasdi — foydalanuvchi to'lagan, admin "tasdiqladi"
    deb hisoblagan, lekin sayt hamon "sotib olmadingiz" derdi."""

    def setUp(self):
        self.user = User.objects.create_user(username='admineditbuyer', password='pass1234')
        self.course = Course.objects.create(
            slug='admin-edit-course', title_uz='Admin Edit Course', type='IT',
            requires_purchase=True, price=200000,
        )
        self.admin = PaymentAdmin(Payment, AdminSite())

    def test_direct_status_edit_creates_course_purchase(self):
        payment = Payment.objects.create(
            user=self.user, kind=Payment.KIND_COURSE, course=self.course, amount=200000,
        )
        payment.status = Payment.STATUS_CONFIRMED

        class FakeForm:
            changed_data = ['status']

        self.admin.save_model(request=None, obj=payment, form=FakeForm(), change=True)

        self.assertTrue(
            CoursePurchase.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_direct_status_edit_extends_subscription(self):
        payment = Payment.objects.create(
            user=self.user, kind=Payment.KIND_SUBSCRIPTION,
            plan='student', duration='week', amount=9000,
        )
        payment.status = Payment.STATUS_CONFIRMED

        class FakeForm:
            changed_data = ['status']

        self.admin.save_model(request=None, obj=payment, form=FakeForm(), change=True)

        self.user.refresh_from_db()
        self.assertEqual(self.user.plan, User.PLAN_STUDENT)
        self.assertIsNotNone(self.user.plan_expires_at)

    def test_editing_other_field_does_not_reapply(self):
        """Status allaqachon 'confirmed', boshqa maydon (admin_note)
        o'zgarsa — qayta ishlov berilmaydi (obuna ikki marta
        uzaytirilib ketmasin)."""
        payment = Payment.objects.create(
            user=self.user, kind=Payment.KIND_COURSE, course=self.course,
            amount=200000, status=Payment.STATUS_CONFIRMED,
        )
        CoursePurchase.objects.filter(user=self.user, course=self.course).delete()

        payment.admin_note = 'izoh qo\'shildi'

        class FakeForm:
            changed_data = ['admin_note']

        self.admin.save_model(request=None, obj=payment, form=FakeForm(), change=True)

        self.assertFalse(
            CoursePurchase.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_creating_already_confirmed_payment_applies_immediately(self):
        """Admin yangi to'lov qo'shib, darhol 'Tasdiqlandi' holatida
        saqlasa (change=False) — bu ham ishlov berilishi kerak."""
        payment = Payment(
            user=self.user, kind=Payment.KIND_COURSE, course=self.course,
            amount=200000, status=Payment.STATUS_CONFIRMED,
        )

        class FakeForm:
            changed_data = ['user', 'kind', 'course', 'amount', 'status']

        self.admin.save_model(request=None, obj=payment, form=FakeForm(), change=False)

        self.assertTrue(
            CoursePurchase.objects.filter(user=self.user, course=self.course).exists()
        )
