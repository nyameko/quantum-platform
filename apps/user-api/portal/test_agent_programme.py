"""M4c: live programme membership is the only source of signed group authority."""

from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase

from portal import agent_client
from portal.models import Person, ProgrammeMembership, ResearchProgramme


class ProgrammeAgentProxyTests(TestCase):
    def setUp(self):
        self.pi = User.objects.create_user(username="programme-pi", password="test")
        self.member = User.objects.create_user(username="programme-member", password="test")
        self.outsider = User.objects.create_user(username="programme-outsider", password="test")
        self.pi_person = Person.objects.create(
            user=self.pi, given_names="PI", family_name="Scientist", institution="CSIR",
        )
        self.member_person = Person.objects.create(
            user=self.member, given_names="Member", family_name="Scientist", institution="CSIR",
        )
        self.programme = ResearchProgramme.objects.create(
            name="Programme for CHSH experiments",
            institution="CSIR",
            description="Test programme", pi=self.pi_person,
            status=ResearchProgramme.Status.ACTIVE,
        )
        ProgrammeMembership.objects.create(
            person=self.pi_person, programme=self.programme,
            role=ProgrammeMembership.Role.PI,
            status=ProgrammeMembership.Status.APPROVED,
        )
        self.membership = ProgrammeMembership.objects.create(
            person=self.member_person, programme=self.programme,
            role=ProgrammeMembership.Role.RESEARCHER,
            status=ProgrammeMembership.Status.APPROVED,
        )
        self.base = f"/api/v1/agent/programmes/{self.programme.pk}/conversations/"
        self.client.force_login(self.pi)

    @patch("portal.agent_api.agent_client.call")
    def test_pi_can_create_room_with_fresh_signed_scope(self, gateway):
        gateway.return_value = {"id": str(uuid4()), "title": "Joint notes"}
        response = self.client.post(
            self.base, data={"title": " Joint notes ", "programme_role": "pi"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(gateway.call_count, 1)
        self.assertEqual(gateway.call_args.kwargs["scope"], "agent:programme")
        self.assertEqual(gateway.call_args.kwargs["programme_id"], self.programme.pk)
        self.assertEqual(gateway.call_args.kwargs["programme_role"], "pi")
        self.assertEqual(gateway.call_args.kwargs["json_body"], {"title": "Joint notes"})

    @patch("portal.agent_api.agent_client.call")
    def test_active_member_reads_and_posts_but_cannot_create(self, gateway):
        self.client.force_login(self.member)
        gateway.return_value = {"items": []}
        self.assertEqual(self.client.get(self.base).status_code, 200)
        self.assertEqual(gateway.call_args.kwargs["programme_role"], "researcher")
        gateway.reset_mock()
        denied = self.client.post(
            self.base, data={"title": "New"},
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, 403)
        gateway.assert_not_called()

        gateway.return_value = {"id": str(uuid4())}
        conv_id = uuid4()
        send = self.client.post(
            self.base + f"{conv_id}/messages/",
            data={"content": {"text": "Discuss CHSH"}, "source_channel": "ssh"},
            content_type="application/json",
        )
        self.assertEqual(send.status_code, 201)
        self.assertEqual(gateway.call_args.kwargs["json_body"]["source_channel"], "web")
        self.assertEqual(gateway.call_args.kwargs["programme_role"], "researcher")

    @patch("portal.agent_api.agent_client.call")
    def test_revoked_user_denied_on_every_endpoint_before_proxy(self, gateway):
        self.client.force_login(self.member)
        self.membership.status = ProgrammeMembership.Status.SUSPENDED
        self.membership.save(update_fields=["status"])
        room_id = uuid4()
        self.assertEqual(self.client.get(self.base).status_code, 404)
        self.assertEqual(self.client.get(self.base + f"{room_id}/").status_code, 404)
        self.assertEqual(self.client.post(
            self.base + f"{room_id}/messages/", data={"content": "test"},
            content_type="application/json",
        ).status_code, 404)
        gateway.assert_not_called()

    @patch("portal.agent_api.agent_client.call")
    def test_outsider_other_programme_and_inactive_programme_denied(self, gateway):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.base).status_code, 404)
        self.client.force_login(self.pi)
        self.assertEqual(self.client.get("/api/v1/agent/programmes/123456/conversations/").status_code, 404)
        self.programme.status = ResearchProgramme.Status.ARCHIVED
        self.programme.save(update_fields=["status"])
        self.assertEqual(self.client.get(self.base).status_code, 404)
        gateway.assert_not_called()

    @patch("portal.agent_api.agent_client.call")
    def test_forged_pi_membership_row_is_not_accepted(self, gateway):
        self.membership.role = ProgrammeMembership.Role.PI
        self.membership.save(update_fields=["role"])
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.base).status_code, 404)
        gateway.assert_not_called()

    def test_raw_programme_assertion_rejects_missing_authority(self):
        with self.assertRaises(agent_client.AgentServiceError):
            agent_client.assertion(self.pi, scope="agent:programme")
        with self.assertRaises(agent_client.AgentServiceError):
            agent_client.assertion(
                self.pi, scope="agent:personal",
                programme_id=self.programme.pk, programme_role="pi",
            )
