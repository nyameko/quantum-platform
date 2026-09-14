from django.contrib.auth.models import User
from django.db import models

class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="person")
    given_names = models.CharField(max_length=150)
    family_name = models.CharField(max_length=150)
    preferred_name = models.CharField(max_length=150, blank=True)
    institution = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    orcid = models.CharField(max_length=19, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["family_name", "given_names"]
        verbose_name = "person"
        verbose_name_plural = "people"

    def __str__(self):
        return self.preferred_name or f"{self.given_names} {self.family_name}"

class ResearchProgramme(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=255, unique=True)
    acronym = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    institution = models.CharField(max_length=255, blank=True)
    pi = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="owned_programmes")
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.acronym} — {self.name}" if self.acronym else self.name

class ProgrammeMembership(models.Model):
    class Role(models.TextChoices):
        PI = "pi", "PI"
        RESEARCHER = "researcher", "Researcher"
        ADMIN = "admin", "Programme Admin"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    programme = models.ForeignKey(ResearchProgramme, on_delete=models.CASCADE, related_name="memberships")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="programme_memberships")
    role = models.CharField(max_length=16, choices=Role, default=Role.RESEARCHER)
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["programme__name", "person__family_name"]
        constraints = [models.UniqueConstraint(
            fields=["programme", "person"], name="unique_programme_membership"
        )]

    def __str__(self):
        return f"{self.person} → {self.programme}"

class SSHKey(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="ssh_keys")
    name = models.CharField(max_length=100)
    public_key = models.TextField()
    fingerprint = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["person__family_name", "name"]
        constraints = [models.UniqueConstraint(
            fields=["person", "name"], name="unique_ssh_key_name_per_person"
        )]

    def __str__(self):
        return f"{self.person} — {self.name}"

class WireGuardKey(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="wireguard_keys")
    name = models.CharField(max_length=100)
    public_key = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["person__family_name", "name"]
        constraints = [models.UniqueConstraint(
            fields=["person", "name"], name="unique_wireguard_key_name_per_person"
        )]

    def __str__(self):
        return f"{self.person} — {self.name}"
