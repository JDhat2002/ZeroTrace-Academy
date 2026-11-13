from django.contrib import admin

from campus.models import (
    Batch,
    CampusAccount,
    CampusCompetition,
    CampusSeat,
    Classroom,
    Department,
    Institution,
    LabControl,
    PracticalExam,
)


class DepartmentInline(admin.TabularInline):
    model = Department
    extra = 0


class CampusAccountInline(admin.TabularInline):
    model = CampusAccount
    extra = 0
    raw_id_fields = ("user",)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "deployment", "status", "plan", "owner")
    list_filter = ("deployment", "status")
    search_fields = ("name", "slug", "owner__email")
    raw_id_fields = ("owner", "plan", "subscription")
    inlines = [DepartmentInline, CampusAccountInline]


@admin.register(CampusSeat)
class CampusSeatAdmin(admin.ModelAdmin):
    list_display = ("user", "institution", "active")
    search_fields = ("user__email", "institution")


admin.site.register(Batch)
admin.site.register(Classroom)
admin.site.register(PracticalExam)
admin.site.register(CampusCompetition)
admin.site.register(LabControl)
