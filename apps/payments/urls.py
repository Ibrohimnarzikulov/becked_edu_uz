"""URLs for payments app."""
from django.urls import path

from .views import (
    SubmitPaymentView,
    MyPaymentsView,
    AdminPaymentListView,
    AdminPaymentActionView,
)

urlpatterns = [
    path('submit/', SubmitPaymentView.as_view(), name='payment-submit'),
    path('my/', MyPaymentsView.as_view(), name='my-payments'),
    path('admin/', AdminPaymentListView.as_view(), name='admin-payments'),
    path('admin/<int:payment_id>/action/', AdminPaymentActionView.as_view(), name='admin-payment-action'),
]