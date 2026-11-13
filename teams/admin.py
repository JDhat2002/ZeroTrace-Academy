from django.contrib import admin

from teams.models import GroupPath, Team, TeamAssignment, TeamCompetition, TeamMember


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    raw_id_fields = ("user",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "plan", "owner")
    list_filter = ("status",)
    search_fields = ("name", "slug", "owner__email")
    raw_id_fields = ("owner", "plan", "subscription")
    inlines = [TeamMemberInline]


admin.site.register(GroupPath)
admin.site.register(TeamAssignment)
admin.site.register(TeamCompetition)
