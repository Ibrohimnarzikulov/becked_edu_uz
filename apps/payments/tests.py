"""Tests for payments app."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

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
        """Admin barcha to'lovlarni ko'radi."""
        Payment.objects.create(user=self.user, plan='student', amount=75000)
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-payments'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

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