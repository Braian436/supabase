from django.test import SimpleTestCase
from django.urls import reverse


class AdminConfigurationTests(SimpleTestCase):
    def test_admin_url_resolves(self):
        response = self.client.get(reverse('admin:index'))

        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('admin:index')}",
            fetch_redirect_response=False,
        )
