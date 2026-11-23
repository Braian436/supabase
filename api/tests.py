from django.test import SimpleTestCase
from django.urls import Resolver404, resolve


class AdminLoginRemovalTests(SimpleTestCase):
    def test_login_and_session_endpoints_are_no_longer_available(self):
        for path in (
            '/api/auth/csrf/',
            '/api/auth/login/',
            '/api/auth/me/',
            '/api/auth/logout/',
        ):
            with self.subTest(path=path):
                with self.assertRaises(Resolver404):
                    resolve(path)
