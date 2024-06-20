from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count
import pytz
from datetime import datetime


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    friends = models.ManyToManyField('self', blank=True)
    photo = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default_profile.jpg')
    other_profile_field = models.CharField(max_length=100, blank=True, null=True)  # Exemple de champ supplémentaire

    def __str__(self):
        return self.user.username

    def add_friend(self, profile):
        self.friends.add(profile)
        profile.friends.add(self)

    def remove_friend(self, profile):
        self.friends.remove(profile)
        profile.friends.remove(self)
    
    def get_photo_url(self):
        if self.photo:
            return self.photo.url
        return '/media/profile_pics/default_profile.jpg'  # Assurez-vous que ce chemin est correct
    
    def get_top_friends(self):
        # Obtenez les participations de l'utilisateur aux sorties
        participations = Participation.objects.filter(membre=self.user, vient=True)

        # Comptez le nombre de fois où chaque ami a participé aux mêmes sorties
        friends_count = (
            participations.values('sortie__participants')
            .annotate(count=Count('sortie__participants'))
            .filter(sortie__participants__profile__in=self.friends.all())
            .exclude(sortie__participants=self.user)
            .order_by('-count')
        )

        # Obtenez les 3 amis avec le plus de participations
        top_friends = []
        for friend in friends_count[:3]:
            top_friends.append(User.objects.get(id=friend['sortie__participants']))

        return top_friends
    
class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='from_user', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='to_user', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.from_user} to {self.to_user}'

class GroupeAmis(models.Model):
    nom = models.CharField(max_length=100)
    createur = models.ForeignKey(User, related_name='groupes_crees', on_delete=models.CASCADE)
    membres = models.ManyToManyField(User, related_name='groupes')
    administrateur = models.ForeignKey(User, related_name='groupes_administres', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.administrateur = self.createur
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom

class Message(models.Model):
    groupe = models.ForeignKey(GroupeAmis, on_delete=models.CASCADE, related_name='messages')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_envoye = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.utilisateur.username}: {self.contenu[:20]}'


class SortieProposee(models.Model):
    groupe = models.ForeignKey(GroupeAmis, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateTimeField(null=True, blank=True)
    lieu = models.CharField(max_length=100)
    createur = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='sorties_participants', through='Participation')
    def is_past_event(self):
        now = datetime.now(pytz.utc)  # Assurez-vous que 'now' est au format aware
        return self.date < now if self.date.tzinfo else self.date < datetime.now()

class DateProposee(models.Model):
    date = models.DateTimeField()
    proposition = models.ForeignKey('PropositionSortie', related_name='dates', on_delete=models.CASCADE)

class PropositionSortie(models.Model):
    groupe = models.ForeignKey(GroupeAmis, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    description = models.TextField()
    lieu = models.CharField(max_length=100)
    createur = models.ForeignKey(User, on_delete=models.CASCADE)
    dates_proposees = models.ManyToManyField(DateProposee, related_name='propositions')

class Vote(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_proposee = models.ForeignKey(DateProposee, on_delete=models.CASCADE)
    vote = models.BooleanField(default=False)

class Participation(models.Model):
    sortie = models.ForeignKey(SortieProposee, on_delete=models.CASCADE)
    membre = models.ForeignKey(User, on_delete=models.CASCADE)
    vient = models.BooleanField(default=False)
    
    
