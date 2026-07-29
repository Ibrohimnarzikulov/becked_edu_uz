"""Admin for payments."""
from django.contrib import admin

from .models import Payment
from .services import apply_confirmed_payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'plan', 'duration', 'course', 'amount', 'status', 'created_at')
    list_filter = ('status', 'kind', 'plan', 'duration')
    search_fields = ('user__username', 'user__full_name')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['confirm_payments', 'reject_payments']

    def save_model(self, request, obj, form, change):
        """To'lov holati "Tasdiqlandi"ga o'zgarganda — bulk "Tasdiqlash"
        action orqalimi yoki forma ichida `status`ni qo'lda tahrirlab
        saqlashmi — farqi yo'q, CoursePurchase/obuna muddati albatta
        yangilanishi kerak. Aks holda admin formada qo'lda "Tasdiqlandi"
        deb saqlasa, foydalanuvchi to'lagan bo'lsa ham kursga/obungaga
        kira olmay qoladi (bu xato production'da haqiqiy foydalanuvchida
        yuz berdi — shuning uchun bu himoya qo'shildi).
        """
        became_confirmed = (
            obj.status == Payment.STATUS_CONFIRMED
            and (not change or 'status' in form.changed_data)
        )
        super().save_model(request, obj, form, change)
        if became_confirmed:
            apply_confirmed_payment(obj)

    @admin.action(description='Tasdiqlash')
    def confirm_payments(self, request, queryset):
        for p in queryset.filter(status=Payment.STATUS_PENDING):
            p.status = Payment.STATUS_CONFIRMED
            apply_confirmed_payment(p)
            p.save()

    @admin.action(description='Rad etish')
    def reject_payments(self, request, queryset):
        queryset.filter(status=Payment.STATUS_PENDING).update(status=Payment.STATUS_REJECTED)
