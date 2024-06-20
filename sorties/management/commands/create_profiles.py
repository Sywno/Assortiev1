from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from sorties.models import Profile

class Command(BaseCommand):
    help = 'Create profiles for users without a profile'

    def handle(self, *args, **kwargs):
        users = User.objects.filter(profile__isnull=True)
        for user in users:
            Profile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f'Profile created for user: {user.username}'))
