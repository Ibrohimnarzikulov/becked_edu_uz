"""Serializers for chat app."""
from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    """Xabar — frontend `is_mine`, `text`, `created_at` kutadi."""
    is_mine = serializers.SerializerMethodField()
    sender = serializers.IntegerField(source='sender_id', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'text', 'sender', 'is_mine', 'created_at')

    def get_is_mine(self, obj):
        user = self.context.get('request').user
        return obj.sender_id == user.id


class ConversationSerializer(serializers.ModelSerializer):
    """Suhbat — suhbatdosh ma'lumoti va oxirgi xabar bilan."""
    partner_username = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            'id', 'partner_username', 'partner_name',
            'last_message', 'last_message_at',
        )

    def _partner(self, obj):
        user = self.context.get('request').user
        return obj.partner_for(user)

    def get_partner_username(self, obj):
        return self._partner(obj).username

    def get_partner_name(self, obj):
        p = self._partner(obj)
        return p.full_name or p.username

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at', '-id').first()
        return last.text if last else ''

    def get_last_message_at(self, obj):
        last = obj.messages.order_by('-created_at', '-id').first()
        return last.created_at if last else obj.updated_at
