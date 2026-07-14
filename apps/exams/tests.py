"""Tests for exams app — testlar, natijalar, reyting."""
from rest_framework.test import APITestCase

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
