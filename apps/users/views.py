"""Views for users app."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdmin
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AdminCreateUserSerializer,
    get_tokens_for_user,
)

User = get_user_model()


class RegisterView(APIView):
    """POST /api/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            # Frontend "error" kalitini kutadi
            error = serializer.errors
            first_field = next(iter(error))
            return Response(
                {'error': error[first_field][0] if error[first_field] else str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            **tokens,
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            err = serializer.errors
            if 'error' in err:
                return Response(err, status=status.HTTP_403_FORBIDDEN if err['error'][0] == 'BLOCKED' else status.HTTP_400_BAD_REQUEST)
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        return Response({
            **tokens,
            'user': UserProfileSerializer(user).data,
        })


class ProfileView(APIView):
    """GET/PATCH /api/auth/profile/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'error': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """POST /api/auth/password/change/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            err = serializer.errors
            first_field = next(iter(err))
            return Response(
                {'error': err[first_field][0] if err[first_field] else str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Parol o\'zgartirildi'})


class AdminUserListView(generics.ListAPIView):
    """GET /api/auth/admin/users/ — faqat admin."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_admin:
            return User.objects.none()
        return User.objects.all().order_by('-date_joined')


class AdminCreateUserView(APIView):
    """POST /api/auth/admin/users/create/ — admin yangi user (o'qituvchi) yaratadi.

    Body: {"username", "password", "full_name", "role"?, "track"?, "grade"?}
    role default = teacher.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AdminCreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            err = serializer.errors
            first_field = next(iter(err))
            return Response(
                {'error': err[first_field][0] if err[first_field] else str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        return Response({
            'detail': 'Foydalanuvchi yaratildi',
            'user': AdminUserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class AdminBlockUserView(APIView):
    """POST /api/auth/admin/users/{id}/block/ — action=block|unblock."""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not request.user.is_admin:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action', 'block')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if user.id == request.user.id:
            return Response({'error': 'O\'zingizni bloklay olmaysiz'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_blocked = (action == 'block')
        user.save(update_fields=['is_blocked'])

        return Response({
            'detail': f'{"Bloklandi" if user.is_blocked else "Blokdan chiqarildi"}',
            'is_blocked': user.is_blocked,
        })


class AdminUserDetailView(APIView):
    """GET /api/auth/admin/users/{id}/ — bitta user tafsilotlari."""
    permission_classes = [IsAdmin]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        return Response(AdminUserSerializer(user).data)


class AdminUserUpdateView(APIView):
    """POST /api/auth/admin/users/{id}/update/ — role va/yoki plan o'zgartirish.

    Body (partial): {"role": "teacher", "plan": "premium"}
    Hech qanday maydon yuborilmasa — 400 (serializer validation xatosi).
    Faqat `role` yuborilsa — faqat rol o'zgaradi.
    Faqat `plan` yuborilsa — faqat plan o'zgaradi.
    """
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            err = serializer.errors
            first_field = next(iter(err))
            return Response(
                {'error': err[first_field][0] if err[first_field] else str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_role = serializer.validated_data.get('role', user.role)

        # ── Self-protection: o'zini adminlikdan chiqarish ──
        if user.id == request.user.id and new_role != User.ROLE_ADMIN:
            return Response(
                {'error': "O'zingizning rolingizni adminlikdan chiqara olmaysiz"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Last-admin protection: tizimda hech bo'lmasa 1 ta admin qolsin ──
        if user.role == User.ROLE_ADMIN and new_role != User.ROLE_ADMIN:
            other_admins_exist = (
                User.objects
                .filter(role=User.ROLE_ADMIN)
                .exclude(id=user.id)
                .exists()
            )
            if not other_admins_exist:
                return Response(
                    {'error': "Tizimda kamida bitta admin bo'lishi kerak"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Saqlash
        serializer.save()

        # Admin qilingan user'ni Django admin'ga ham kiritish (mavjud `make_admin` bilan bir xil)
        if new_role == User.ROLE_ADMIN and not user.is_staff:
            user.is_staff = True
            user.save(update_fields=['is_staff'])

        return Response({
            'detail': 'Foydalanuvchi yangilandi',
            'user': AdminUserSerializer(user).data,
        })


class AdminStatsView(APIView):
    """GET /api/auth/admin/stats/ — dashboard statistikasi.

    Userlar, to'lovlar va kurslar bo'yicha aggregate ma'lumot.
    Frontend admin dashboard uchun.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        from apps.payments.models import Payment
        from apps.courses.models import Course, Lesson, LessonProgress

        users = User.objects.all()
        payments = Payment.objects.all()
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)

        return Response({
            'users': {
                'total': users.count(),
                'by_role': {
                    'admin': users.filter(role=User.ROLE_ADMIN).count(),
                    'teacher': users.filter(role=User.ROLE_TEACHER).count(),
                    'student': users.filter(role=User.ROLE_STUDENT).count(),
                },
                'by_plan': {
                    'free': users.filter(plan=User.PLAN_FREE).count(),
                    'student': users.filter(plan=User.PLAN_STUDENT).count(),
                    'premium': users.filter(plan=User.PLAN_PREMIUM).count(),
                },
                'blocked': users.filter(is_blocked=True).count(),
                'new_today': users.filter(date_joined__date=today).count(),
                'new_this_week': users.filter(date_joined__gte=week_ago).count(),
            },
            'payments': {
                'total': payments.count(),
                'pending': payments.filter(status=Payment.STATUS_PENDING).count(),
                'confirmed': payments.filter(status=Payment.STATUS_CONFIRMED).count(),
                'rejected': payments.filter(status=Payment.STATUS_REJECTED).count(),
            },
            'courses': {
                'total_courses': Course.objects.count(),
                'active_courses': Course.objects.filter(is_active=True).count(),
                'total_lessons': Lesson.objects.count(),
                'total_progress': LessonProgress.objects.count(),
            },
        })
