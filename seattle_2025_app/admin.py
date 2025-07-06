from django.contrib import admin
from nomnom.nominate.admin import CustomUserAdmin

from .models import ControllPerson


class ControllPersonInline(admin.StackedInline):
    model = ControllPerson

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    readonly_fields = ["perid", "newperid"]


CustomUserAdmin.inlines.append(ControllPersonInline)
