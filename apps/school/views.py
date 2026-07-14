"""Views for school app — fanlar, vazifalar, to'garaklar, maktab testlari."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subject, Assignment, Circle
from .serializers import SubjectSerializer, AssignmentSerializer, CircleSerializer

from apps.exams.models import Test
from apps.exams.serializers import TestSerializer


class SubjectListView(APIView):
    """GET /api/school/subjects/."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Subject.objects.filter(is_active=True)
        return Response(SubjectSerializer(qs, many=True).data)


class AssignmentListView(APIView):
    """GET /api/school/assignments/."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Assignment.objects.select_related('subject')
        return Response(AssignmentSerializer(qs, many=True).data)


class CircleListView(APIView):
    """GET /api/school/circles/."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Circle.objects.filter(is_active=True)
        return Response(CircleSerializer(qs, many=True).data)


class SchoolTestListView(APIView):
    """GET /api/school/tests/ — faqat 'School' turidagi testlar."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Test.objects.filter(type=Test.TYPE_SCHOOL)
        return Response(TestSerializer(qs, many=True).data)
