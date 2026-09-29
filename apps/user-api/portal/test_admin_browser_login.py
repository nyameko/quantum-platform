from django.test import TestCase, override_settings


class AdminBrowserLoginContractTests(TestCase):
    @override_settings(ALLOWED_HOSTS=["admin.quantum.nyameko.com", "testserver"])
    def test_admin_redirects_anonymous_browser_to_login(self):
        response = self.client.get(
            "/admin/",
            HTTP_HOST="admin.quantum.nyameko.com",
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    @override_settings(ALLOWED_HOSTS=["admin.quantum.nyameko.com", "testserver"])
    def test_allauth_browser_login_page_renders(self):
        response = self.client.get(
            "/accounts/login/?next=%2Fadmin%2F",
            HTTP_HOST="admin.quantum.nyameko.com",
        )
        self.assertEqual(response.status_code, 200)
