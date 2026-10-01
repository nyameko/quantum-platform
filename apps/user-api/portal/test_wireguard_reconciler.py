import base64

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from portal.models import Person, WireGuardKey


@override_settings(
    WIREGUARD_RECONCILER_TOKEN="reconcile-secret",
    WIREGUARD_CLIENT_POOL="192.0.2.0/29",
    WIREGUARD_RESERVED_ADDRESSES={"192.0.2.1"},
)
class WireGuardReconcilerApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nlisa",
            email="nlisa@example.invalid",
            password="test",
        )
        self.person = Person.objects.create(
            user=self.user,
            given_names="Nyameko",
            family_name="Lisa",
        )
        self.key = WireGuardKey.objects.create(
            person=self.person,
            name="blackmyth",
            public_key=base64.b64encode(bytes(range(32))).decode("ascii"),
            active=True,
        )

    def _auth(self):
        return {"HTTP_AUTHORIZATION": "Bearer reconcile-secret"}

    def test_reconciler_allocates_address_but_does_not_mark_provisioned(self):
        response = self.client.get(
            "/api/v1/internal/wireguard/peers/",
            **self._auth(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.key.refresh_from_db()
        self.assertEqual(self.key.assigned_address, "192.0.2.2/32")
        self.assertIsNone(self.key.provisioned_at)
        self.assertEqual(
            response.json()["peers"][0]["allowed_ip"],
            "192.0.2.2/32",
        )

    def test_acknowledgement_marks_active_peer_provisioned(self):
        self.key.assigned_address = "192.0.2.2/32"
        self.key.save(update_fields=["assigned_address"])
        response = self.client.post(
            "/api/v1/internal/wireguard/reconciled/",
            data={"peer_ids": [self.key.pk]},
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.key.refresh_from_db()
        self.assertIsNotNone(self.key.provisioned_at)

    def test_reconciler_rejects_missing_token(self):
        response = self.client.get("/api/v1/internal/wireguard/peers/")
        self.assertEqual(response.status_code, 403)
