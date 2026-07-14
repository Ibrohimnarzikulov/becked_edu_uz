"""Tests for chat app."""
from rest_framework.test import APITestCase

from apps.users.models import User


class ChatTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='stud', password='pass1234', role='student')
        self.teacher = User.objects.create_user(username='teach', password='pass1234', role='teacher')

    def _auth(self, user):
        res = self.client.post('/api/auth/login/', {'username': user.username, 'password': 'pass1234'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + res.data['access'])

    def test_conversation_auto_provisioned(self):
        """Student uchun o'qituvchi bilan suhbat avtomatik yaratiladi."""
        self._auth(self.student)
        res = self.client.get('/api/chat/conversations/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['partner_username'], 'teach')

    def test_send_and_read_message(self):
        """Xabar yuborish va o'qish, is_mine bayrog'i."""
        self._auth(self.student)
        conv_id = self.client.get('/api/chat/conversations/').data[0]['id']
        res = self.client.post(f'/api/chat/conversations/{conv_id}/messages/', {'text': 'Salom'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data['is_mine'])
        msgs = self.client.get(f'/api/chat/conversations/{conv_id}/messages/').data
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'Salom')

    def test_empty_message_rejected(self):
        self._auth(self.student)
        conv_id = self.client.get('/api/chat/conversations/').data[0]['id']
        res = self.client.post(f'/api/chat/conversations/{conv_id}/messages/', {'text': '  '}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_cannot_access_foreign_conversation(self):
        """Boshqaning suhbatiga kirib bo'lmaydi — 404."""
        self._auth(self.student)
        res = self.client.get('/api/chat/conversations/99999/messages/')
        self.assertEqual(res.status_code, 404)
