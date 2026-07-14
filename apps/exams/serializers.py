"""Serializers for exams app."""
from rest_framework import serializers

from .models import Test, Score


class TestSerializer(serializers.ModelSerializer):
    """Test — savollari bilan (frontend `questions` massivini kutadi)."""
    class Meta:
        model = Test
        fields = ('id', 'title', 'subject', 'type', 'questions', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_questions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("questions massiv bo'lishi kerak")
        return value


class ScoreSerializer(serializers.ModelSerializer):
    """Natija — foydalanuvchi va test id bilan."""
    user = serializers.IntegerField(source='user_id', read_only=True)
    test = serializers.IntegerField(source='test_id', read_only=True)

    class Meta:
        model = Score
        fields = ('id', 'user', 'test', 'score', 'created_at')
