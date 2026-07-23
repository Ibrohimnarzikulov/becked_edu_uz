"""Tests for users app."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


class AuthTests(TestCase):
    """Ro'yxatdan o'tish, login, profil testlari."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')

    def test_register_success(self):
        """Muvaffaqiyatli ro'yxatdan o'tish."""
        data = {
            'username': 'testuser',
            'password': 'test1234',
            'full_name': 'Test User',
            'track': 'Frontend',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'student')
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_register_username_too_short(self):
        """Username 3 ta belgidan kam bo'lsa, xato."""
        data = {
            'username': 'ab',
            'password': 'test1234',
            'full_name': 'Test User',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_username_with_space(self):
        """Username bo'sh joy bo'lsa, xato."""
        data = {
            'username': 'test user',
            'password': 'test1234',
            'full_name': 'Test User',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_duplicate_username(self):
        """Bir xil username bilan 2-marta ro'yxatdan o'tish — xato."""
        User.objects.create_user(username='testuser', password='test1234')
        data = {
            'username': 'testuser',
            'password': 'test1234',
            'full_name': 'Test User',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_login_success(self):
        """Login to'g'ri ishlaydi."""
        User.objects.create_user(username='testuser', password='test1234')
        data = {'username': 'testuser', 'password': 'test1234'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_login_wrong_password(self):
        """Noto'g'ri parol bilan login — 400."""
        User.objects.create_user(username='testuser', password='test1234')
        data = {'username': 'testuser', 'password': 'wrong'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_login_blocked_user(self):
        """Bloklangan user login qila olmaydi."""
        user = User.objects.create_user(username='testuser', password='test1234')
        user.is_blocked = True
        user.save()
        data = {'username': 'testuser', 'password': 'test1234'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'][0], 'BLOCKED')

    def test_profile_requires_auth(self):
        """Profile ko'rish uchun login kerak."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 401)

    def test_profile_get(self):
        """Login qilib profile ko'rish."""
        user = User.objects.create_user(
            username='testuser', password='test1234', full_name='Test User',
        )
        self.client.force_authenticate(user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')

    def test_profile_update(self):
        """Profilni yangilash."""
        user = User.objects.create_user(
            username='testuser', password='test1234', full_name='Test',
        )
        self.client.force_authenticate(user)
        response = self.client.patch(
            self.profile_url,
            {'full_name': 'Updated Name', 'bio': 'New bio'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.full_name, 'Updated Name')
        self.assertEqual(user.bio, 'New bio')

    def test_change_password(self):
        """Parol o'zgartirish."""
        user = User.objects.create_user(
            username='testuser', password='old1234',
        )
        self.client.force_authenticate(user)
        response = self.client.post(
            reverse('change-password'),
            {'current_password': 'old1234', 'new_password': 'new1234'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('new1234'))

    def test_change_password_wrong_current(self):
        """Noto'g'ri joriy parol — xato."""
        user = User.objects.create_user(
            username='testuser', password='old1234',
        )
        self.client.force_authenticate(user)
        response = self.client.post(
            reverse('change-password'),
            {'current_password': 'wrong', 'new_password': 'new1234'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)


class AdminTests(TestCase):
    """Admin panel testlari — foydalanuvchini bloklash."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student', password='student1234',
            role=User.ROLE_STUDENT,
        )

    def test_admin_can_list_users(self):
        """Admin barcha userlarni ko'ra oladi."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-users'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_student_cannot_list_users(self):
        """Student boshqa userlarni ko'ra olmaydi."""
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse('admin-users'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_admin_can_block_user(self):
        """Admin user bloklashi mumkin."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-block-user', kwargs={'user_id': self.student.id}),
            {'action': 'block'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_blocked)

    def test_admin_can_unblock_user(self):
        """Admin user blokdan chiqarishi mumkin."""
        self.student.is_blocked = True
        self.student.save()
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-block-user', kwargs={'user_id': self.student.id}),
            {'action': 'unblock'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_blocked)

    def test_admin_cannot_block_self(self):
        """Admin o'zini bloklay olmaydi."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-block-user', kwargs={'user_id': self.admin.id}),
            {'action': 'block'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)


class AdminRoleTests(TestCase):
    """Admin — rol o'zgartirish, stats, detail endpoint testlari."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )
        self.admin2 = User.objects.create_user(
            username='admin2', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )
        self.teacher = User.objects.create_user(
            username='teacher1', password='teacher1234',
            role=User.ROLE_TEACHER,
        )
        self.student = User.objects.create_user(
            username='student1', password='student1234',
            role=User.ROLE_STUDENT, plan=User.PLAN_FREE,
        )

    # ── Update role/plan ──
    def test_admin_can_change_role(self):
        """Admin student rolini teacher'ga o'zgartira oladi."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.student.id}),
            {'role': 'teacher'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.ROLE_TEACHER)

    def test_admin_can_change_plan(self):
        """Admin free plan'ni premium'ga o'zgartira oladi."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.student.id}),
            {'plan': 'premium'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.plan, User.PLAN_PREMIUM)

    def test_admin_can_change_role_and_plan_together(self):
        """Admin role va plan'ni bir vaqtda o'zgartira oladi."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.student.id}),
            {'role': 'teacher', 'plan': 'premium'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.ROLE_TEACHER)
        self.assertEqual(self.student.plan, User.PLAN_PREMIUM)

    def test_making_admin_sets_is_staff(self):
        """role=admin bo'lganda is_staff=True ga o'rnatilishi kerak."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.student.id}),
            {'role': 'admin'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_staff)

    def test_invalid_role_rejected(self):
        """Noto'g'ri role qiymati — 400."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.student.id}),
            {'role': 'superuser'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_empty_body_rejected(self):
        """Bo'sh body — 400 (kamida bitta maydon kerak)."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.student.id}),
            {},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_user_not_found(self):
        """User topilmasa — 404."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': 99999}),
            {'role': 'teacher'},
            format='json',
        )
        self.assertEqual(response.status_code, 404)

    def test_non_admin_cannot_update(self):
        """Admin bo'lmagan user yangilay olmaydi — 403."""
        self.client.force_authenticate(self.student)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.teacher.id}),
            {'role': 'admin'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_update(self):
        """Login qilmagan user — 401."""
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.student.id}),
            {'role': 'teacher'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    def test_admin_cannot_demote_self(self):
        """Admin o'zini demote qila olmaydi."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.admin.id}),
            {'role': 'teacher'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_admin_cannot_demote_last_admin(self):
        """Faqat 1 ta admin bo'lsa, uni demote qilib bo'lmaydi."""
        self.admin2.delete()
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.admin.id}),
            {'role': 'teacher'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_can_demote_when_others_exist(self):
        """Boshqa admin bo'lsa, demote mumkin."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse('admin-update-user', kwargs={'user_id': self.admin2.id}),
            {'role': 'teacher'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.admin2.refresh_from_db()
        self.assertEqual(self.admin2.role, User.ROLE_TEACHER)

    # ── Detail ──
    def test_admin_can_get_user_detail(self):
        """Admin bitta user tafsilotini ko'ra oladi."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse('admin-user-detail', kwargs={'user_id': self.student.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'student1')

    def test_non_admin_cannot_get_user_detail(self):
        """Admin bo'lmagan user detail ko'ra olmaydi — 403."""
        self.client.force_authenticate(self.student)
        response = self.client.get(
            reverse('admin-user-detail', kwargs={'user_id': self.teacher.id}),
        )
        self.assertEqual(response.status_code, 403)

    # ── Stats ──
    def test_admin_can_get_stats(self):
        """Admin statistika olishi mumkin."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('admin-stats'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.data)
        self.assertIn('payments', response.data)
        self.assertIn('courses', response.data)
        self.assertEqual(response.data['users']['total'], 4)
        self.assertEqual(response.data['users']['by_role']['admin'], 2)
        self.assertEqual(response.data['users']['by_role']['teacher'], 1)
        self.assertEqual(response.data['users']['by_role']['student'], 1)

    def test_non_admin_cannot_get_stats(self):
        """Admin bo'lmagan user stats olishi mumkin emas — 403."""
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse('admin-stats'))
        self.assertEqual(response.status_code, 403)

class AdminCreateUserTests(TestCase):
    """Admin yangi foydalanuvchi (o'qituvchi/admin) yaratadi."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', password='admin1234',
            role=User.ROLE_ADMIN, is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student', password='student1234',
            role=User.ROLE_STUDENT,
        )

    def test_admin_creates_teacher(self):
        """Admin o'qituvchi yaratadi (default role=teacher)."""
        self.client.force_authenticate(self.admin)
        res = self.client.post(reverse('admin-create-user'), {
            'username': 'Yangi_Ustoz', 'password': 'pass1234', 'full_name': 'Yangi Ustoz',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['user']['role'], 'teacher')
        u = User.objects.get(username='yangi_ustoz')  # username kichik harfda
        self.assertTrue(u.check_password('pass1234'))
        self.assertEqual(u.role, 'teacher')

    def test_admin_creates_admin_sets_staff(self):
        """role=admin bo'lsa is_staff=True bo'ladi."""
        self.client.force_authenticate(self.admin)
        res = self.client.post(reverse('admin-create-user'), {
            'username': 'yordamchi', 'password': 'pass1234', 'full_name': 'Yordamchi Admin', 'role': 'admin',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        u = User.objects.get(username='yordamchi')
        self.assertEqual(u.role, 'admin')
        self.assertTrue(u.is_staff)

    def test_student_cannot_create_user(self):
        """Oddiy user yarata olmaydi — 403."""
        self.client.force_authenticate(self.student)
        res = self.client.post(reverse('admin-create-user'), {
            'username': 'x123', 'password': 'pass1234', 'full_name': 'X',
        }, format='json')
        self.assertEqual(res.status_code, 403)

    def test_duplicate_username_rejected(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(reverse('admin-create-user'), {
            'username': 'student', 'password': 'pass1234', 'full_name': 'Dup',
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_unauthenticated_cannot_create(self):
        res = self.client.post(reverse('admin-create-user'), {
            'username': 'x123', 'password': 'pass1234', 'full_name': 'X',
        }, format='json')
        self.assertEqual(res.status_code, 401)


class DjRestAuthTests(TestCase):
    """dj-rest-auth endpointlari — JWT bilan ishlashi kerak."""

    def setUp(self):
        self.client = APIClient()

    def _make_user(self):
        user = User.objects.create_user(
            username='restauth', password='pass1234', full_name='Rest Auth'
        )
        res = self.client.post(
            reverse('login'), {'username': 'restauth', 'password': 'pass1234'}, format='json'
        )
        return user, res.data['access']

    def test_registration_returns_jwt(self):
        """POST /api/auth/registration/ — JWT access/refresh qaytaradi."""
        res = self.client.post('/api/auth/registration/', {
            'username': 'yangiuser',
            'password1': 'juda-kuchli-parol-99',
            'password2': 'juda-kuchli-parol-99',
            'full_name': 'Yangi User',
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

        user = User.objects.get(username='yangiuser')
        self.assertEqual(user.role, User.ROLE_STUDENT)
        self.assertEqual(user.full_name, 'Yangi User')

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user(username='band', password='pass1234')
        res = self.client.post('/api/auth/registration/', {
            'username': 'band',
            'password1': 'juda-kuchli-parol-99',
            'password2': 'juda-kuchli-parol-99',
            'full_name': 'Band User',
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_user_details_endpoint(self):
        """GET /api/auth/user/ — JWT bilan foydalanuvchi ma'lumotlari."""
        user, token = self._make_user()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get('/api/auth/user/')
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data['username'], 'restauth')
        self.assertIn('avatar_url', res.data)
        self.assertEqual(res.data['role'], 'student')

    def test_user_details_requires_auth(self):
        res = self.client.get('/api/auth/user/')
        self.assertEqual(res.status_code, 401)

    def test_custom_login_still_wins(self):
        """Loyihaning o'z /api/auth/login/ endpointi dj-rest-auth'nikini bosib o'tadi."""
        User.objects.create_user(username='ustun', password='pass1234')
        res = self.client.post(
            reverse('login'), {'username': 'ustun', 'password': 'pass1234'}, format='json'
        )
        self.assertEqual(res.status_code, 200)
        # O'z endpointimiz `user` obyektini ham qaytaradi — dj-rest-auth qaytarmaydi.
        self.assertIn('user', res.data)
        self.assertIn('access', res.data)


class AvatarUploadTests(TestCase):
    """Profil rasmini yuklash."""

    def setUp(self):
        self.client = APIClient()
        User.objects.create_user(username='rasmli', password='pass1234')
        res = self.client.post(
            reverse('login'), {'username': 'rasmli', 'password': 'pass1234'}, format='json'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    @staticmethod
    def _png():
        """1x1 shaffof PNG."""
        import base64
        from django.core.files.uploadedfile import SimpleUploadedFile
        raw = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
            'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        )
        return SimpleUploadedFile('avatar.png', raw, content_type='image/png')

    def test_upload_avatar(self):
        res = self.client.patch(
            reverse('profile'), {'avatar': self._png()}, format='multipart'
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIsNotNone(res.data['avatar_url'])
        self.assertIn('/media/avatars/', res.data['avatar_url'])

        user = User.objects.get(username='rasmli')
        self.assertTrue(user.avatar)
        user.avatar.delete(save=True)

    def test_avatar_url_is_none_by_default(self):
        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.data['avatar_url'])

    def test_avatar_rejects_non_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        bad = SimpleUploadedFile('not.png', b'hello world', content_type='image/png')
        res = self.client.patch(reverse('profile'), {'avatar': bad}, format='multipart')
        self.assertEqual(res.status_code, 400)
