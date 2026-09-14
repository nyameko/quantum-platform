from django.contrib import admin
from .models import Person, ProgrammeMembership, ResearchProgramme, SSHKey, WireGuardKey

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("family_name", "given_names", "institution", "user")
    search_fields = ("family_name", "given_names", "preferred_name", "institution", "user__username", "user__email")
    list_filter = ("institution",)
    ordering = ("family_name", "given_names")

@admin.register(ResearchProgramme)
class ResearchProgrammeAdmin(admin.ModelAdmin):
    list_display = ("name", "acronym", "pi", "institution", "status")
    search_fields = ("name", "acronym", "institution", "pi__family_name")
    list_filter = ("status", "institution")
    autocomplete_fields = ("pi",)

@admin.register(ProgrammeMembership)
class ProgrammeMembershipAdmin(admin.ModelAdmin):
    list_display = ("programme", "person", "role", "status", "requested_at", "approved_at")
    search_fields = ("programme__name", "person__family_name", "person__given_names", "person__user__email")
    list_filter = ("status", "role")
    autocomplete_fields = ("programme", "person")
    date_hierarchy = "requested_at"

@admin.register(SSHKey)
class SSHKeyAdmin(admin.ModelAdmin):
    list_display = ("person", "name", "fingerprint", "active", "created_at")
    search_fields = ("person__family_name", "person__given_names", "fingerprint", "name")
    list_filter = ("active",)
    autocomplete_fields = ("person",)

@admin.register(WireGuardKey)
class WireGuardKeyAdmin(admin.ModelAdmin):
    list_display = ("person", "name", "public_key", "active", "created_at")
    search_fields = ("person__family_name", "person__given_names", "public_key", "name")
    list_filter = ("active",)
    autocomplete_fields = ("person",)
