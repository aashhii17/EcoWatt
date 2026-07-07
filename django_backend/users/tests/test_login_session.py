from django.test import Client, TestCase
from django.contrib.auth.models import User
from users.models import UserProfile

class LoginSessionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser@example.com', email='testuser@example.com', password='TestPassword123')
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            contact_number='1234567890',
            physical_address='123 Test Street'
        )

    def test_login_and_access_protected_page(self):
        # Login with contact number and password
        login_response = self.client.post('/login/', {
            'contact_no': '1234567890',
            'password': 'TestPassword123',
            'captchaInput': 'dummy'  # Bypass captcha validation for test
        })
        # Check redirect after login
        self.assertEqual(login_response.status_code, 302)
        self.assertIn('/dashboard/', login_response.url)

        # Access protected page after login
        dashboard_response = self.client.get('/dashboard/')
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'Test User')

        # Access add_appliances page
        appliances_response = self.client.get('/add_appliances/')
        self.assertEqual(appliances_response.status_code, 200)

if __name__ == '__main__':
    import unittest
    unittest.main()
