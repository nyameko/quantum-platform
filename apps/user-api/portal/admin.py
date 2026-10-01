from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import (
    AuditEvent,
    ExecutionRecord,
    Person,
    PIApplication,
    ProgrammeMembership,
    ResearchProgramme,
    SSHKey,
    WireGuardKey,
)
from .programme_services import (
    ApprovalError,
    approve_pi_application_record,
    reject_pi_application_record,
)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "family_name",
        "given_names",
        "institution",
        "user",
        "posix_uid",
        "posix_gid",
        "posix_provisioned_at",
    )
    search_fields = (
        "family_name",
        "given_names",
        "preferred_name",
        "institution",
        "user__username",
        "user__email",
    )
    list_filter = ("institution",)
    ordering = ("family_name", "given_names")
    autocomplete_fields = ("user",)


@admin.register(ResearchProgramme)
class ResearchProgrammeAdmin(admin.ModelAdmin):
    list_display = ("name", "acronym", "pi", "institution", "status")
    search_fields = (
        "name",
        "acronym",
        "institution",
        "pi__family_name",
    )
    list_filter = ("status", "institution")
    autocomplete_fields = ("pi",)


@admin.register(ProgrammeMembership)
class ProgrammeMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "programme",
        "person",
        "role",
        "status",
        "requested_at",
        "approved_at",
    )
    search_fields = (
        "programme__name",
        "programme__acronym",
        "person__family_name",
        "person__given_names",
        "person__user__username",
        "person__user__email",
    )
    list_filter = ("status", "role")
    autocomplete_fields = ("programme", "person")
    date_hierarchy = "requested_at"


@admin.register(PIApplication)
class PIApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "programme_name",
        "programme_acronym",
        "applicant",
        "institution",
        "status",
        "created_at",
        "reviewed_at",
    )
    search_fields = (
        "programme_name",
        "programme_acronym",
        "institution",
        "applicant__family_name",
        "applicant__given_names",
        "applicant__user__username",
        "applicant__user__email",
    )
    list_filter = ("status", "institution")
    autocomplete_fields = ("applicant",)
    readonly_fields = (
        "programme_acronym",
        "status",
        "reviewed_at",
        "reviewed_by",
    )
    date_hierarchy = "created_at"
    actions = ("approve_selected", "reject_selected")

    @admin.action(description="Approve selected PI applications")
    def approve_selected(self, request, queryset):
        approved = 0
        for application in queryset:
            try:
                approve_pi_application_record(application, request.user)
                approved += 1
            except ApprovalError as exc:
                self.message_user(
                    request,
                    f"{application}: {exc}",
                    level=messages.WARNING,
                )
        if approved:
            self.message_user(
                request,
                f"Approved {approved} PI application(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="Reject selected PI applications")
    def reject_selected(self, request, queryset):
        rejected = 0
        for application in queryset:
            try:
                reject_pi_application_record(application, request.user)
                rejected += 1
            except ApprovalError as exc:
                self.message_user(
                    request,
                    f"{application}: {exc}",
                    level=messages.WARNING,
                )
        if rejected:
            self.message_user(
                request,
                f"Rejected {rejected} PI application(s).",
                level=messages.SUCCESS,
            )


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "actor",
        "object_type",
        "object_id",
        "created_at",
    )
    search_fields = (
        "event_type",
        "object_type",
        "object_id",
        "actor__email",
    )
    list_filter = ("event_type", "object_type")
    readonly_fields = (
        "actor",
        "event_type",
        "object_type",
        "object_id",
        "metadata",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SSHKey)
class SSHKeyAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "name",
        "fingerprint",
        "active",
        "created_at",
    )
    search_fields = (
        "person__family_name",
        "person__given_names",
        "fingerprint",
        "name",
    )
    list_filter = ("active",)
    autocomplete_fields = ("person",)


@admin.register(WireGuardKey)
class WireGuardKeyAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "name",
        "public_key",
        "active",
        "created_at",
    )
    search_fields = (
        "person__family_name",
        "person__given_names",
        "public_key",
        "name",
    )
    list_filter = ("active",)
    autocomplete_fields = ("person",)


# Make platform identity administration explicit in the Quantum Platform admin
# rather than relying on an opaque default registration.
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class PlatformUserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
        "last_login",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("username",)



@admin.register(ExecutionRecord)
class ExecutionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "offering",
        "state",
        "scheduler_job_id",
        "scheduler_state",
        "created_at",
        "finished_at",
    )
    search_fields = ("id", "user__username", "scheduler_job_id", "offering")
    list_filter = ("offering", "state", "scheduler_state")
    readonly_fields = (
        "id",
        "user",
        "offering",
        "state",
        "scheduler_job_id",
        "scheduler_state",
        "scheduler_node",
        "parameters",
        "result_path",
        "error_message",
        "submitted_at",
        "finished_at",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
