"""Admin for payments."""
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__full_name')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['confirm_payments', 'reject_payments']

    @admin.action(description='Tasdiqlash')
    def confirm_payments(self, request, queryset):
        for p in queryset.filter(status=Payment.STATUS_PENDING):
            p.status = Payment.STATUS_CONFIRMED
            p.user.plan = p.plan
            p.user.save(update_fields=['plan'])
            p.save()

    @admin.action(description='Rad etish')
    def reject_payments(self, request, queryset):
        queryset.filter(status=Payment.STATUS_PENDING).update(status=Payment.STATUS_REJECTED)