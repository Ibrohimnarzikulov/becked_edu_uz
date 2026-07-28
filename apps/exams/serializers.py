"""Serializers for exams app."""
from rest_framework import serializers

from .models import Test, Score


class TestSerializer(serializers.ModelSerializer):
    """Test — savollari bilan (frontend `questions` massivini kutadi)."""
    course_id = serializers.IntegerField(read_only=True)
    course_title = serializers.CharField(source='course.title_uz', read_only=True, default=None)

    class Meta:
        model = Test
        fields = ('id', 'title', 'subject', 'type', 'questions',
                   'course', 'course_id', 'course_title', 'created_at')
        read_only_fields = ('id', 'created_at', 'course_id', 'course_title')
        extra_kwargs = {'course': {'write_only': True, 'required': False, 'allow_null': True}}

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
