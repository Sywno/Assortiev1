from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import GroupeAmis, SortieProposee, PropositionSortie, DateProposee, Vote, Participation
from .forms import SortieProposeeForm
from .models import Profile, FriendRequest
from django.utils import timezone
from datetime import timedelta


class SimpleTestCase(TestCase):

    def setUp(self):
        # Créez un utilisateur de test
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client = Client()
        self.client.login(username='testuser', password='12345')

        # Créez un groupe et une sortie pour les tests
        self.groupe = GroupeAmis.objects.create(nom='Test Groupe', createur=self.user, administrateur=self.user)
        self.sortie = SortieProposee.objects.create(
            groupe=self.groupe,
            nom='Test Sortie',
            description='Test Description',
            lieu='Test Lieu',
            createur=self.user
        )
        self.proposition = PropositionSortie.objects.create(
            groupe=self.groupe,
            nom='Test Proposition',
            description='Test Description',
            lieu='Test Lieu',
            createur=self.user
        )
        self.date_proposee = DateProposee.objects.create(
            proposition=self.proposition,
            date='2024-06-15T12:00:00Z'
        )

    def test_groupe_detail_view(self):
        response = self.client.get(reverse('groupe_detail', kwargs={'group_id': self.groupe.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Groupe')


    def test_proposer_sortie_view(self):
        response = self.client.get(reverse('proposer_sortie', kwargs={'group_id': self.groupe.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proposer une Sortie')  # Modifiez cette ligne

    def test_vote(self):
        vote_data = {
            'proposition_id': self.proposition.id,
            f'vote_{self.proposition.id}': self.date_proposee.id
        }
        response = self.client.post(reverse('groupe_detail', kwargs={'group_id': self.groupe.id}), vote_data)
        self.assertEqual(response.status_code, 302)  # Redirection après vote
        self.assertTrue(Vote.objects.filter(utilisateur=self.user, date_proposee=self.date_proposee).exists())

    def test_toggle_participation(self):
        participation_data = {
            'form_id': self.sortie.id,
            'vient': 'True'
        }
        response = self.client.post(reverse('groupe_detail', kwargs={'group_id': self.groupe.id}), participation_data)
        self.assertEqual(response.status_code, 302)  # Redirection après participation
        self.assertTrue(Participation.objects.filter(membre=self.user, sortie=self.sortie, vient=True).exists())


class GroupeAmisTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser2', password='12345')

    def test_groupe_creation(self):
        groupe = GroupeAmis.objects.create(nom='Test Groupe 2', createur=self.user, administrateur=self.user)
        self.assertEqual(groupe.nom, 'Test Groupe 2')
        self.assertEqual(groupe.createur, self.user)


class SortieProposeeFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.groupe = GroupeAmis.objects.create(nom='Test Groupe', createur=self.user)
        self.valid_data = {
            'nom': 'Test Sortie',
            'description': 'Une description de test',
            'date': (timezone.now() + timedelta(days=1)).isoformat(),  # Date dans le futur
            'lieu': 'Un lieu de test',
            'groupe': self.groupe.id,
            'createur': self.user.id,
        }

    def test_sortie_proposee_form_valid(self):
        form = SortieProposeeForm(data=self.valid_data)
        if not form.is_valid():
            print(form.errors)  # Ajoutez cette ligne pour afficher les erreurs du formulaire
        self.assertTrue(form.is_valid())
        
        
class FriendRequestTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='12345')
        self.user2 = User.objects.create_user(username='user2', password='12345')

    def test_send_friend_request(self):
        self.client.login(username='user1', password='12345')
        response = self.client.post(reverse('send_friend_request', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FriendRequest.objects.filter(from_user=self.user1, to_user=self.user2).exists())

    def test_accept_friend_request(self):
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        self.client.login(username='user2', password='12345')
        friend_request = FriendRequest.objects.get(from_user=self.user1, to_user=self.user2)
        response = self.client.post(reverse('accept_friend_request', kwargs={'request_id': friend_request.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user1.profile.friends.filter(id=self.user2.profile.id).exists())
        self.assertTrue(self.user2.profile.friends.filter(id=self.user1.profile.id).exists())