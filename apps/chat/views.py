"""Views for chat app."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

User = get_user_model()


def _reachable_users(user):
    """Foydalanuvchi kim bilan suhbatlasha oladi.

    - Student  → o'qituvchi va adminlar bilan
    - Teacher/Admin → barcha (o'zidan boshqa) bilan
    """
    qs = User.objects.exclude(id=user.id).filter(is_active=True, is_blocked=False)
    if getattr(user, 'is_student_user', False):
        qs = qs.filter(role__in=[User.ROLE_TEACHER, User.ROLE_ADMIN])
    return qs


def _ensure_conversations(user):
    """Foydalanuvchi uchun suhbatdoshlar bilan suhbat mavjudligini ta'minlaydi."""
    for partner in _reachable_users(user):
        Conversation.between(user, partner)


class ConversationListView(APIView):
    """GET /api/chat/conversations/ — suhbatlar ro'yxati (avto-yaratiladi)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _ensure_conversations(request.user)
        qs = Conversation.objects.filter(
            Q(user_a=request.user) | Q(user_b=request.user)
        ).prefetch_related('messages', 'user_a', 'user_b')
        data = ConversationSerializer(qs, many=True, context={'request': request}).data
        # Oxirgi xabar vaqti bo'yicha saralash (bo'sh suhbatlar oxirida)
        data.sort(key=lambda c: c['last_message_at'] or '', reverse=True)
        return Response(data)


class MessageListView(APIView):
    """GET/POST /api/chat/conversations/{id}/messages/."""
    permission_classes = [IsAuthenticated]

    def _get_conversation(self, request, conv_id):
        try:
            conv = Conversation.objects.get(id=conv_id)
        except Conversation.DoesNotExist:
            return None
        if request.user.id not in (conv.user_a_id, conv.user_b_id):
            return None
        return conv

    def get(self, request, conv_id):
        conv = self._get_conversation(request, conv_id)
        if conv is None:
            return Response({'error': 'Suhbat topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        # Suhbatdosh yozgan xabarlarni o'qilgan deb belgilash
        conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        msgs = conv.messages.all()
        return Response(MessageSerializer(msgs, many=True, context={'request': request}).data)

    def post(self, request, conv_id):
        conv = self._get_conversation(request, conv_id)
        if conv is None:
            return Response({'error': 'Suhbat topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        text = (request.data.get('text') or '').strip()
        if not text:
            return Response({'error': 'Xabar bo\'sh bo\'lishi mumkin emas'}, status=status.HTTP_400_BAD_REQUEST)

        msg = Message.objects.create(conversation=conv, sender=request.user, text=text)
        conv.save(update_fields=['updated_at'])  # updated_at yangilanadi
        return Response(
            MessageSerializer(msg, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
