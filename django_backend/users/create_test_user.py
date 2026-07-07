import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import UserProfile

def create_test_user():
    # Create test user
    user, created = User.objects.get_or_create(username='testuser@example.com', email='testuser@example.com')
    if created:
        user.set_password('TestPassword123')
        user.save()
    # Create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': 'Test User',
            'contact_number': '1234567890',
            'physical_address': '123 Test Street'
        }
    )
    if created:
        profile.save()
    print("Test user created with username: testuser@example.com and password: TestPassword123")

if __name__ == '__main__':
    create_test_user()
