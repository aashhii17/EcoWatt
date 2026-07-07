from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile

class Command(BaseCommand):
    help = 'Create superuser admin account'

    def handle(self, *args, **kwargs):
        email = 'admin@example.com'
        password = 'Aashi'
        contact_number = '9874563210'

        user, created = User.objects.get_or_create(username=email, defaults={'email': email, 'is_staff': True, 'is_superuser': True})
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        profile, prof_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': 'System Administrator',
                'contact_number': contact_number,
                'physical_address': 'Headquarters Control Room'
            }
        )
        if not prof_created and profile.contact_number != contact_number:
            profile.contact_number = contact_number
            profile.save()

        self.stdout.write(self.style.SUCCESS(f'Admin user created successfully! Email/Username: {email}, Contact No: {contact_number}, Password: {password}'))
