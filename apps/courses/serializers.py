"""Serializers for courses app."""
from rest_framework import serializers

from .models import Course, Lesson, Test, Question, Choice, LessonProgress


class ChoiceSerializer(serializers.ModelSerializer):
    """Test varianti — faqat matn (to'g'ri javob ko'rinmaydi)."""
    class Meta:
        model = Choice
        fields = ('id', 'text_uz', 'text_ru', 'text_en', 'order')

    def to_representation(self, instance):
        # Frontend "options" maydonini kutadi
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'text': data['text_uz'],
        }


class QuestionSerializer(serializers.ModelSerializer):
    """Test savoli — variantlar bilan."""
    options = ChoiceSerializer(source='choices', many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'text_uz', 'options', 'order')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'q': data['text_uz'],
            'options': data['options'],
        }


class TestDetailSerializer(serializers.ModelSerializer):
    """Test — savollar va variantlar."""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = ('id', 'title_uz', 'subject', 'type', 'questions')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'title': data['title_uz'],
            'subject': data['subject'],
            'type': data['type'],
            'questions': data['questions'],
        }


class LessonProgressSerializer(serializers.ModelSerializer):
    """Dars holati (ichki)."""
    class Meta:
        model = LessonProgress
        fields = ('status', 'last_score', 'watched_at')


class LessonSerializer(serializers.ModelSerializer):
    """Dars — progress bilan."""
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ('id', 'title_uz', 'youtube_id', 'duration', 'order', 'progress')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'title': data['title_uz'],
            'youtubeId': data['youtube_id'],
            'duration': data['duration'],
            'order': data['order'],
            'progress': data['progress'],
        }

    def get_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {'status': 'locked', 'last_score': None}
        try:
            prog = obj.progress.get(user=request.user)
            return {
                'status': prog.status,
                'last_score': prog.last_score,
                'watched_at': prog.watched_at,
            }
        except LessonProgress.DoesNotExist:
            return {'status': 'locked', 'last_score': None}


class CourseListSerializer(serializers.ModelSerializer):
    """Kurs — darslar bilan."""
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'slug', 'title_uz', 'icon', 'type', 'lessons')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'slug': data['slug'],
            'title': data['title_uz'],
            'icon': data['icon'],
            'type': data['type'],
            'lessons': data['lessons'],
        }


class TestSubmitSerializer(serializers.Serializer):
    """Test javoblarini qabul qilish."""
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='{question_id: choice_id}',
    )