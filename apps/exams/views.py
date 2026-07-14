"""Views for exams app — testlar, natijalar, reyting."""
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Test, Score
from .serializers import TestSerializer, ScoreSerializer

User = get_user_model()


def _is_staff_role(user):
    return getattr(user, 'is_admin', False) or getattr(user, 'is_teacher', False)


class TestListCreateView(APIView):
    """GET /api/tests/ — ro'yxat; POST /api/tests/ — yaratish (o'qituvchi/admin)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Test.objects.all()
        type_filter = request.query_params.get('type')
        if type_filter:
            qs = qs.filter(type=type_filter)
        return Response(TestSerializer(qs, many=True).data)

    def post(self, request):
        if not _is_staff_role(request.user):
            return Response({'error': "Ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        test = serializer.save(created_by=request.user)
        return Response(TestSerializer(test).data, status=status.HTTP_201_CREATED)


class TestDetailView(APIView):
    """GET/DELETE /api/tests/{id}/."""
    permission_classes = [IsAuthenticated]

    def get(self, request, test_id):
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TestSerializer(test).data)

    def delete(self, request, test_id):
        if not _is_staff_role(request.user):
            return Response({'error': "Ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyScoresView(APIView):
    """GET /api/scores/my/ — foydalanuvchining natijalari."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Score.objects.filter(user=request.user).select_related('test')
        return Response(ScoreSerializer(qs, many=True).data)


class ScoresView(APIView):
    """GET /api/scores/ — barcha natijalar (o'qituvchi/admin); POST — natija saqlash."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_staff_role(request.user):
            return Response({'error': "Ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)
        qs = Score.objects.select_related('user', 'test')
        return Response(ScoreSerializer(qs, many=True).data)

    def post(self, request):
        # student berilsa va so'rovchi staff bo'lsa — o'sha student uchun; aks holda o'zi uchun
        student_id = request.data.get('student')
        if student_id and _is_staff_role(request.user):
            try:
                target = User.objects.get(id=student_id)
            except (User.DoesNotExist, ValueError, TypeError):
                return Response({'error': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        else:
            target = request.user

        test_id = request.data.get('test')
        try:
            test = Test.objects.get(id=test_id)
        except (Test.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        try:
            score_val = max(0, min(100, int(request.data.get('score', 0))))
        except (ValueError, TypeError):
            return Response({'error': "Ball noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)

        score, _created = Score.objects.update_or_create(
            user=target, test=test, defaults={'score': score_val}
        )
        return Response(ScoreSerializer(score).data, status=status.HTTP_201_CREATED)


class LeaderboardView(APIView):
    """GET /api/leaderboard/?track=IT|School — o'quvchilar reytingi."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        track = request.query_params.get('track')  # IT | School | None
        scores = Score.objects.all()
        if track:
            scores = scores.filter(test__type=track)

        # Har bir student uchun o'rtacha ball va test soni
        agg = (
            scores.filter(user__role=User.ROLE_STUDENT)
            .values('user_id', 'user__username', 'user__full_name', 'user__role')
            .annotate(avg_score=Avg('score'), test_count=Count('id'))
        )
        by_user = {row['user_id']: row for row in agg}

        # Ball topshirmagan studentlarni ham qo'shamiz (0 ball bilan)
        result = []
        for u in User.objects.filter(role=User.ROLE_STUDENT, is_active=True):
            row = by_user.get(u.id)
            result.append({
                'uid': str(u.id),
                'id': u.id,
                'username': u.username,
                'full_name': u.full_name or u.username,
                'role': u.role,
                'avg_score': round(row['avg_score']) if row else 0,
                'test_count': row['test_count'] if row else 0,
            })

        result.sort(key=lambda r: (r['avg_score'], r['test_count']), reverse=True)
        return Response(result)
