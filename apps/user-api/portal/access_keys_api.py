import base64
import binascii
import hashlib
import struct

from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AuditEvent, SSHKey, WireGuardKey


SSH_KEY_TYPES = {
    "ssh-ed25519",
    "ssh-rsa",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "sk-ssh-ed25519@openssh.com",
    "sk-ecdsa-sha2-nistp256@openssh.com",
}


def _audit(actor, event_type, obj=None, metadata=None):
    AuditEvent.objects.create(
        actor=actor,
        event_type=event_type,
        object_type=obj.__class__.__name__ if obj else "",
        object_id=str(obj.pk) if obj and obj.pk else "",
        metadata=metadata or {},
    )


def _person(request):
    person = getattr(request.user, "person", None)
    if person is None:
        return None, Response(
            {"detail": "Complete your research profile before adding access keys."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return person, None


def _name(value):
    name = str(value or "").strip()
    if not name:
        raise ValueError("Key name is required.")
    if len(name) > 100:
        raise ValueError("Key name must be 100 characters or fewer.")
    return name


def _ssh_public_key(value):
    public_key = " ".join(str(value or "").strip().split())
    parts = public_key.split(" ", 2)
    if len(parts) < 2:
        raise ValueError("Enter a complete OpenSSH public key.")

    key_type, encoded = parts[0], parts[1]
    if key_type not in SSH_KEY_TYPES:
        raise ValueError("Unsupported SSH public-key type.")

    try:
        blob = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise ValueError("SSH public-key data is not valid base64.") from exc

    if len(blob) < 4:
        raise ValueError("SSH public-key data is truncated.")

    type_length = struct.unpack(">I", blob[:4])[0]
    embedded_type = blob[4:4 + type_length].decode("ascii", errors="strict")
    if embedded_type != key_type:
        raise ValueError("SSH key type does not match the encoded key.")

    digest = base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii").rstrip("=")
    fingerprint = f"SHA256:{digest}"
    return public_key, fingerprint


def _wireguard_public_key(value):
    public_key = str(value or "").strip()
    try:
        decoded = base64.b64decode(public_key.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise ValueError("WireGuard public key is not valid base64.") from exc

    if len(decoded) != 32:
        raise ValueError("WireGuard public keys must decode to exactly 32 bytes.")

    return base64.b64encode(decoded).decode("ascii")


def _ssh_payload(key):
    return {
        "id": key.id,
        "name": key.name,
        "public_key": key.public_key,
        "fingerprint": key.fingerprint,
        "active": key.active,
        "created_at": key.created_at,
    }


def _wireguard_payload(key):
    return {
        "id": key.id,
        "name": key.name,
        "public_key": key.public_key,
        "active": key.active,
        "created_at": key.created_at,
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def ssh_keys(request):
    person, error = _person(request)
    if error:
        return error

    if request.method == "GET":
        keys = person.ssh_keys.order_by("-active", "-created_at")
        return Response([_ssh_payload(key) for key in keys])

    try:
        name = _name(request.data.get("name"))
        public_key, fingerprint = _ssh_public_key(request.data.get("public_key"))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if SSHKey.objects.filter(person=person, name=name).exists():
        return Response(
            {"detail": "You already have an SSH key with this name."},
            status=status.HTTP_409_CONFLICT,
        )
    if SSHKey.objects.filter(fingerprint=fingerprint).exists():
        return Response(
            {"detail": "This SSH public key is already registered."},
            status=status.HTTP_409_CONFLICT,
        )

    try:
        with transaction.atomic():
            key = SSHKey.objects.create(
                person=person,
                name=name,
                public_key=public_key,
                fingerprint=fingerprint,
                active=True,
            )
            _audit(
                request.user,
                "SSH_KEY_REGISTERED",
                key,
                metadata={"fingerprint": fingerprint},
            )
    except IntegrityError:
        return Response(
            {"detail": "Unable to register duplicate SSH key."},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(_ssh_payload(key), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_ssh_key(request, key_id):
    person, error = _person(request)
    if error:
        return error

    key = SSHKey.objects.filter(pk=key_id, person=person).first()
    if key is None:
        return Response({"detail": "SSH key not found."}, status=status.HTTP_404_NOT_FOUND)

    if key.active:
        key.active = False
        key.save(update_fields=["active"])
        _audit(
            request.user,
            "SSH_KEY_REVOKED",
            key,
            metadata={"fingerprint": key.fingerprint},
        )

    return Response(_ssh_payload(key))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def wireguard_keys(request):
    person, error = _person(request)
    if error:
        return error

    if request.method == "GET":
        keys = person.wireguard_keys.order_by("-active", "-created_at")
        return Response([_wireguard_payload(key) for key in keys])

    try:
        name = _name(request.data.get("name"))
        public_key = _wireguard_public_key(request.data.get("public_key"))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if WireGuardKey.objects.filter(person=person, name=name).exists():
        return Response(
            {"detail": "You already have a WireGuard key with this name."},
            status=status.HTTP_409_CONFLICT,
        )
    if WireGuardKey.objects.filter(public_key=public_key).exists():
        return Response(
            {"detail": "This WireGuard public key is already registered."},
            status=status.HTTP_409_CONFLICT,
        )

    try:
        with transaction.atomic():
            key = WireGuardKey.objects.create(
                person=person,
                name=name,
                public_key=public_key,
                active=True,
            )
            _audit(request.user, "WIREGUARD_KEY_REGISTERED", key)
    except IntegrityError:
        return Response(
            {"detail": "Unable to register duplicate WireGuard key."},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(_wireguard_payload(key), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_wireguard_key(request, key_id):
    person, error = _person(request)
    if error:
        return error

    key = WireGuardKey.objects.filter(pk=key_id, person=person).first()
    if key is None:
        return Response(
            {"detail": "WireGuard key not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if key.active:
        key.active = False
        key.save(update_fields=["active"])
        _audit(request.user, "WIREGUARD_KEY_REVOKED", key)

    return Response(_wireguard_payload(key))
