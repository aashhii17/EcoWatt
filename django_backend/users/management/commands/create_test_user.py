from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile

class Command(BaseCommand):
    help = 'Create a test user with profile'

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(username='testuser@example.com', email='testuser@example.com')
        if created:
            user.set_password('TestPassword123')
            user.save()
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
        self.stdout.write(self.style.SUCCESS('Test user created with username: testuser@example.com and password: TestPassword123'))
