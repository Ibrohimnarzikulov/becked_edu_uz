"""Admin for users."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'full_name', 'role', 'plan', 'is_blocked', 'is_staff', 'date_joined')
    list_filter = ('role', 'plan', 'is_blocked', 'is_staff', 'is_superuser')
    search_fields = ('username', 'full_name', 'track', 'grade')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('EduHub ma\'lumotlari', {
            'fields': ('role', 'full_name', 'bio', 'track', 'grade', 'plan', 'is_blocked'),
        }),
    )

    actions = ['block_users', 'unblock_users', 'make_admin', 'change_role_action']

    @admin.action(description='Bloklash')
    def block_users(self, request, queryset):
        count = queryset.exclude(id=request.user.id).update(is_blocked=True)

    @admin.action(description='Blokdan chiqarish')
    def unblock_users(self, request, queryset):
        count = queryset.update(is_blocked=False)

    @admin.action(description='Admin qilish')
    def make_admin(self, request, queryset):
        count = queryset.update(role=User.ROLE_ADMIN, is_staff=True)

    @admin.action(description='Rolni o\'zgartirish')
    def change_role_action(self, request, queryset):
        """Tanlangan userlar uchun rol tanlash formasi ko'rsatadi."""
        # Form submit qilinganida
        if 'apply' in request.POST:
            new_role = request.POST.get('new_role')
            if new_role not in dict(User.ROLE_CHOICES):
                self.message_user(request, 'Noto\'g\'ri rol tanlandi', level='error')
                return HttpResponseRedirect(request.get_full_path())

            updated = 0
            for user in queryset:
                # Self-protection: o'zini adminlikdan chiqarishni bloklash
                if user.id == request.user.id and new_role != User.ROLE_ADMIN:
                    self.message_user(
                        request,
                        f"O'zingizning rolingizni o'zgartira olmaysiz: {user.username}",
                        level='error',
                    )
                    continue

                # Last-admin protection: kamida 1 ta admin qolsin
                if user.role == User.ROLE_ADMIN and new_role != User.ROLE_ADMIN:
                    if not User.objects.filter(role=User.ROLE_ADMIN).exclude(id=user.id).exists():
                        self.message_user(
                            request,
                            f"Tizimda kamida 1 ta admin bo'lishi kerak: {user.username}",
                            level='error',
                        )
                        continue

                user.role = new_role
                if new_role == User.ROLE_ADMIN:
                    user.is_staff = True
                user.save(update_fields=['role', 'is_staff'])
                updated += 1

            if updated:
                self.message_user(request, f'{updated} ta foydalanuvchi yangilandi')
            return HttpResponseRedirect(request.get_full_path())

        # Birinchi marta — forma ko'rsatamiz
        context = {
            'title': 'Rolni o\'zgartirish',
            'users': queryset,
            'role_choices': User.ROLE_CHOICES,
            'action': 'change_role_action',
            'opts': self.model._meta,
        }
        return render(request, 'admin/users/change_role.html', context)
