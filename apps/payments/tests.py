"""Tests for payments app."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.courses.models import Course, CoursePurchase
from apps.users.models import User
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
        """To'lov so'rovini yuborish."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'plan': 'student', 'amount': 75000},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.first()
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.plan, 'student')

    def test_submit_payment_wrong_amount(self):
        """Noto'g'ri summa bilan yuborish — xato."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'plan': 'student', 'amount': 50000},  # 75000 bo'lishi kerak
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_submit_payment_free_not_allowed(self):
        """Free tarif uchun to'lov yuborilmaydi."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse('payment-submit'),
            {'plan': 'free', 'amount': 0},
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
