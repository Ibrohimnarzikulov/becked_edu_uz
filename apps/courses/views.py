"""Views for courses app."""
from datetime import date
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin

from .models import Course, Lesson, Test, Question, Choice, LessonProgress
from .serializers import (
    CourseListSerializer,
    TestDetailSerializer,
    LessonProgressSerializer,
    TestSubmitSerializer,
)


# ── FREE PLAN LIMIT ────────────────────────────────
FREE_DAILY_LIMIT = 3


class CourseListView(APIView):
    """GET /api/courses/?type=IT"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Course.objects.filter(is_active=True).prefetch_related('lessons__progress')
        course_type = request.query_params.get('type')
        if course_type:
            qs = qs.filter(type=course_type)
        serializer = CourseListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class DailyLimitView(APIView):
    """GET /api/courses/daily-limit/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Premium va Student — cheksiz
        if user.plan in (user.PLAN_STUDENT, user.PLAN_PREMIUM):
            return Response({
                'watched_count': 0,
                'remaining': 999,
                'limit': None,
                'plan': user.plan,
            })

        # Free — bugun ko'rilgan darslar soni
        today = date.today()
        watched_today = LessonProgress.objects.filter(
            user=user,
            watched_at__date=today,
            status__in=[LessonProgress.STATUS_WATCHED, LessonProgress.STATUS_PASSED],
        ).count()

        return Response({
            'watched_count': watched_today,
            'remaining': max(0, FREE_DAILY_LIMIT - watched_today),
            'limit': FREE_DAILY_LIMIT,
            'plan': user.plan,
        })


class WatchLessonView(APIView):
    """POST /api/courses/lessons/{id}/watch/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        user = request.user
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Premium/Student — cheksiz
        if user.plan not in (user.PLAN_STUDENT, user.PLAN_PREMIUM):
            # Free — limitni tekshirish
            from django.utils import timezone
            today = date.today()
            watched_today = LessonProgress.objects.filter(
                user=user,
                watched_at__date=today,
                status__in=[LessonProgress.STATUS_WATCHED, LessonProgress.STATUS_PASSED],
            ).exclude(lesson=lesson).count()

            if watched_today >= FREE_DAILY_LIMIT:
                return Response({
                    'error': 'daily_limit',
                    'message': 'Kunlik limit tugadi. Premium tarifga o\'ting.',
                }, status=status.HTTP_403_FORBIDDEN)

        # Progress saqlash
        from django.utils import timezone
        progress, _ = LessonProgress.objects.get_or_create(
            user=user, lesson=lesson,
        )
        if progress.status == LessonProgress.STATUS_LOCKED:
            progress.status = LessonProgress.STATUS_WATCHED
        progress.watched_at = timezone.now()
        progress.save()

        # Bugungi holat
        if user.plan in (user.PLAN_STUDENT, user.PLAN_PREMIUM):
            daily = {'watched_count': 0, 'remaining': 999, 'limit': None, 'plan': user.plan}
        else:
            today = date.today()
            count = LessonProgress.objects.filter(
                user=user,
                watched_at__date=today,
                status__in=[LessonProgress.STATUS_WATCHED, LessonProgress.STATUS_PASSED],
            ).count()
            daily = {
                'watched_count': count,
                'remaining': max(0, FREE_DAILY_LIMIT - count),
                'limit': FREE_DAILY_LIMIT,
                'plan': user.plan,
            }

        has_test = hasattr(lesson, 'test')

        return Response({
            'daily': daily,
            'has_test': has_test,
        })


class LessonTestView(APIView):
    """GET /api/courses/lessons/{id}/test/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        try:
            test = lesson.test
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TestDetailSerializer(test)
        return Response(serializer.data)


class SubmitTestView(APIView):
    """POST /api/courses/lessons/{id}/test/submit/"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, lesson_id):
        user = request.user
        lesson = get_object_or_404(Lesson, id=lesson_id)
        try:
            test = lesson.test
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TestSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

        answers = serializer.validated_data['answers']
        questions = test.questions.prefetch_related('choices')

        if not questions.exists():
            return Response({'error': 'Testda savollar yo\'q'}, status=status.HTTP_400_BAD_REQUEST)

        correct = 0
        total = questions.count()
        details = []

        for q in questions:
            user_choice_id = answers.get(str(q.id))
            correct_choice = q.choices.filter(is_correct=True).first()
            is_correct = (user_choice_id is not None and int(user_choice_id) == correct_choice.id)
            if is_correct:
                correct += 1
            details.append({
                'question_id': q.id,
                'correct_choice_id': correct_choice.id if correct_choice else None,
                'is_correct': is_correct,
            })

        score = int((correct / total) * 100) if total else 0

        # Progress yangilash
        progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
        progress.last_score = score
        progress.status = LessonProgress.STATUS_PASSED if score >= 50 else LessonProgress.STATUS_WATCHED
        progress.save()

        return Response({
            'score': score,
            'correct': correct,
            'total': total,
            'passed': score >= 50,
            'letter': (
                'A' if score >= 86 else
                'B' if score >= 71 else
                'C' if score >= 56 else
                'D' if score >= 41 else 'F'
            ),
            'details': details,
        })


class AdminLessonTestView(APIView):
    """GET/POST /api/courses/admin/lessons/{id}/test/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        if not request.user.is_admin:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)
        lesson = get_object_or_404(Lesson, id=lesson_id)
        try:
            test = lesson.test
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TestDetailSerializer(test).data)

    def post(self, request, lesson_id):
        if not request.user.is_admin:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)
        # Kelajakda test yaratish/tahrirlash uchun
        return Response({'detail': 'Tayyor (POST hali qo\'llanilmaydi)'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdminCourseListView(APIView):
    """GET /api/courses/admin/ — barcha kurslar (jumladan noaktiv).

    Oddiy GET /api/courses/ faqat `is_active=True` qaytaradi. Admin
    uchun noaktiv va tartibsiz kurslarni ham ko'rish kerak.
    Query params: ?type=IT|School
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Course.objects.all().prefetch_related('lessons__progress')
        course_type = request.query_params.get('type')
        if course_type:
            qs = qs.filter(type=course_type)
        return Response(CourseListSerializer(qs, many=True, context={'request': request}).data)


class AdminLessonProgressListView(APIView):
    """GET /api/courses/admin/progress/ — barcha LessonProgress.

    Query params:
        ?user_id=<int>     — faqat shu user
        ?lesson_id=<int>   — faqat shu dars
        ?status=passed|watched|locked
        ?course_id=<int>   — shu kursga tegishli darslar
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = LessonProgress.objects.select_related('user', 'lesson__course').order_by('-updated_at')

        user_id = request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)

        lesson_id = request.query_params.get('lesson_id')
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)

        course_id = request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(lesson__course_id=course_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        data = [
            {
                'id': p.id,
                'user_id': p.user_id,
                'username': p.user.username,
                'lesson_id': p.lesson_id,
                'lesson_title': p.lesson.title_uz,
                'course_id': p.lesson.course_id,
                'course_title': p.lesson.course.title_uz,
                'status': p.status,
                'last_score': p.last_score,
                'watched_at': p.watched_at,
                'updated_at': p.updated_at,
            }
            for p in qs[:500]  # Maksimal 500 ta — sahifalash kelajakda
        ]
        return Response({'count': qs.count(), 'results': data})