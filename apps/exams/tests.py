"""Tests for exams app — testlar, natijalar, reyting."""
from rest_framework.test import APITestCase

from apps.courses.models import Course, CoursePurchase
from apps.users.models import User
from .models import Test


class ExamsTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='teach', password='pass1234', role='teacher')
        self.student = User.objects.create_user(username='stud', password='pass1234', role='student')

    def _auth(self, user):
        res = self.client.post('/api/auth/login/', {'username': user.username, 'password': 'pass1234'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + res.data['access'])

    def test_teacher_creates_test_student_cannot(self):
        payload = {'title': 'T1', 'subject': 'Math', 'type': 'School',
                   'questions': [{'q': '2+2?', 'options': ['3', '4'], 'answer': 1}]}
        self._auth(self.student)
        self.assertEqual(self.client.post('/api/tests/', payload, format='json').status_code, 403)
        self._auth(self.teacher)
        res = self.client.post('/api/tests/', payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(len(res.data['questions']), 1)

    def test_save_score_and_leaderboard(self):
        test = Test.objects.create(title='T', type='IT', questions=[])
        self._auth(self.student)
        res = self.client.post('/api/scores/', {'test': test.id, 'score': 80}, format='json')
        self.assertEqual(res.status_code, 201)
        # /scores/my/
        my = self.client.get('/api/scores/my/').data
        self.assertEqual(len(my), 1)
        self.assertEqual(my[0]['score'], 80)
        # leaderboard
        lb = self.client.get('/api/leaderboard/').data
        me = [r for r in lb if r['username'] == 'stud'][0]
        self.assertEqual(me['avg_score'], 80)
        self.assertEqual(me['test_count'], 1)

    def test_score_updates_not_duplicates(self):
        test = Test.objects.create(title='T', type='IT', questions=[])
        self._auth(self.student)
        self.client.post('/api/scores/', {'test': test.id, 'score': 50}, format='json')
        self.client.post('/api/scores/', {'test': test.id, 'score': 95}, format='json')
        my = self.client.get('/api/scores/my/').data
        self.assertEqual(len(my), 1)
        self.assertEqual(my[0]['score'], 95)

    def test_leaderboard_track_filter(self):
        it = Test.objects.create(title='IT', type='IT', questions=[])
        sch = Test.objects.create(title='S', type='School', questions=[])
        self._auth(self.student)
        self.client.post('/api/scores/', {'test': it.id, 'score': 40}, format='json')
        self.client.post('/api/scores/', {'test': sch.id, 'score': 100}, format='json')
        me_it = [r for r in self.client.get('/api/leaderboard/?track=IT').data if r['username'] == 'stud'][0]
        self.assertEqual(me_it['avg_score'], 40)
        me_sch = [r for r in self.client.get('/api/leaderboard/?track=School').data if r['username'] == 'stud'][0]
        self.assertEqual(me_sch['avg_score'], 100)


class CourseGatedTestsTests(APITestCase):
    """Kursga bog'liq (course FK) mustaqil testlar — faqat sotib olganlarga."""

    def setUp(self):
        self.student = User.objects.create_user(username='buyer2', password='pass1234', role='student')
        self.admin = User.objects.create_user(
            username='examadmin', password='pass1234', role='admin', is_staff=True,
        )
        self.course = Course.objects.create(
            slug='backend2', title_uz='Backend', type='IT',
            requires_purchase=True, price=400000,
        )
        self.locked_test = Test.objects.create(
            title='Backend testi', type='IT', questions=[], course=self.course,
        )
        self.open_test = Test.objects.create(title='Ochiq test', type='IT', questions=[])

    def _auth(self, user):
        res = self.client.post('/api/auth/login/', {'username': user.username, 'password': 'pass1234'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + res.data['access'])

    def test_locked_test_hidden_from_list_without_purchase(self):
        self._auth(self.student)
        titles = [t['title'] for t in self.client.get('/api/tests/').data]
        self.assertIn('Ochiq test', titles)
        self.assertNotIn('Backend testi', titles)

    def test_locked_test_visible_after_purchase(self):
        CoursePurchase.objects.create(user=self.student, course=self.course)
        self._auth(self.student)
        titles = [t['title'] for t in self.client.get('/api/tests/').data]
        self.assertIn('Backend testi', titles)

    def test_locked_test_detail_blocked_without_purchase(self):
        self._auth(self.student)
        res = self.client.get(f'/api/tests/{self.locked_test.id}/')
        self.assertEqual(res.status_code, 403)

    def test_admin_sees_locked_test_without_purchase(self):
        self._auth(self.admin)
        titles = [t['title'] for t in self.client.get('/api/tests/').data]
        self.assertIn('Backend testi', titles)
