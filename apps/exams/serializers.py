"""Serializers for exams app."""
from rest_framework import serializers

from .models import Test, Score


class TestSerializer(serializers.ModelSerializer):
    """Test — savollari bilan (frontend `questions` massivini kutadi).

    Kursga bog'liq (`course.requires_purchase`) test sotib olinmagan
    bo'lsa, ro'yxatdan yashirilmaydi — `locked=True` bilan qaytadi va
    `questions` bo'sh bo'ladi, shunda frontend "🔒 Sotib oling" holatini
    ko'rsata oladi (butunlay yo'q qilib yubormay).
    """
    course_id = serializers.IntegerField(read_only=True)
    course_title = serializers.CharField(source='course.title_uz', read_only=True, default=None)
    course_price = serializers.IntegerField(source='course.price', read_only=True, default=None)
    locked = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = ('id', 'title', 'subject', 'type', 'questions', 'course',
                   'course_id', 'course_title', 'course_price', 'locked', 'created_at')
        read_only_fields = ('id', 'created_at', 'course_id', 'course_title', 'course_price', 'locked')
        extra_kwargs = {'course': {'write_only': True, 'required': False, 'allow_null': True}}

    def get_locked(self, obj):
        return obj.id in self.context.get('locked_test_ids', set())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['locked']:
            data['questions'] = []
        return data

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
