"""Views for payments app."""
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentSubmitSerializer,
    AdminActionSerializer,
)


class SubmitPaymentView(APIView):
    """POST /api/payments/submit/ — FormData (plan, amount, screenshot)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            err = serializer.errors
            first_field = next(iter(err))
            return Response(
                {'error': err[first_field][0] if err[first_field] else str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        payment = Payment.objects.create(
            user=request.user,
            plan=data['plan'],
            amount=data['amount'],
            screenshot=data.get('screenshot'),
        )

        return Response({
            'detail': "To'lov so'rovi yuborildi. Admin tasdiqlashini kuting.",
            'payment': PaymentSerializer(payment, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class MyPaymentsView(APIView):
    """GET /api/payments/my/ — foydalanuvchi tarixi."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(user=request.user)
        return Response(PaymentSerializer(payments, many=True, context={'request': request}).data)


class AdminPaymentListView(APIView):
    """GET /api/payments/admin/?status=pending — barcha to'lovlar."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        status_filter = request.query_params.get('status')
        qs = Payment.objects.select_related('user').order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(PaymentSerializer(qs, many=True, context={'request': request}).data)


class AdminPaymentActionView(APIView):
    """POST /api/payments/admin/{id}/action/ — confirm/reject."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, payment_id):
        if not request.user.is_admin:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        try:
            payment = Payment.objects.select_for_update().get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({'error': "To'lov topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if payment.status != Payment.STATUS_PENDING:
            return Response({'error': 'Bu to\'lov allaqachon ko\'rib chiqilgan'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdminActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']
        note = serializer.validated_data.get('note', '')

        if action == 'confirm':
            payment.status = Payment.STATUS_CONFIRMED
            # User tarifini yangilash
            payment.user.plan = payment.plan
            payment.user.save(update_fields=['plan'])
        else:
            payment.status = Payment.STATUS_REJECTED

        payment.admin_note = note
        payment.save()

        return Response({
            'detail': 'Tasdiqlandi' if action == 'confirm' else 'Rad etildi',
            'payment': PaymentSerializer(payment, context={'request': request}).data,
        })