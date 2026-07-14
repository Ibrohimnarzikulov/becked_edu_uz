"""Tests for school app."""
from rest_framework.test import APITestCase

from apps.users.models import User
from .models import Subject, Assignment, Circle
from apps.exams.models import Test


class SchoolTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='stud', password='pass1234', role='student')
        res = self.client.post('/api/auth/login/', {'username': 'stud', 'password': 'pass1234'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + res.data['access'])

    def test_empty_lists_ok(self):
        for ep in ['subjects', 'assignments', 'circles', 'tests']:
            res = self.client.get(f'/api/school/{ep}/')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data, [])

    def test_subjects_and_assignments(self):
        subj = Subject.objects.create(name='Matematika', icon='🔢')
        Assignment.objects.create(subject=subj, title='Uy vazifa', status='pending')
        subjects = self.client.get('/api/school/subjects/').data
        self.assertEqual(subjects[0]['name'], 'Matematika')
        assigns = self.client.get('/api/school/assignments/').data
        self.assertEqual(assigns[0]['subject'], subj.id)
        self.assertEqual(assigns[0]['status'], 'pending')

    def test_circles(self):
        Circle.objects.create(name='Robototexnika', members=12, schedule='Dush/Chor')
        circles = self.client.get('/api/school/circles/').data
        self.assertEqual(circles[0]['name'], 'Robototexnika')
        self.assertEqual(circles[0]['members'], 12)

    def test_school_tests_only_school_type(self):
        Test.objects.create(title='IT test', type='IT', questions=[])
        Test.objects.create(title='Maktab test', type='School', questions=[])
        tests = self.client.get('/api/school/tests/').data
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0]['title'], 'Maktab test')
