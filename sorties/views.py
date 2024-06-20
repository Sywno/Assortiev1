from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Profile, FriendRequest, GroupeAmis, SortieProposee, Participation, PropositionSortie, DateProposee, Vote
from .forms import GroupeAmisForm, SortieProposeeForm, ParticipationForm, ProfileForm, UserForm, CustomUserCreationForm, AddMemberForm, PropositionSortieForm, DateProposeeForm

import json, pytz




@login_required
def remove_friend(request, friend_id):
    friend_profile = get_object_or_404(Profile, id=friend_id)
    user_profile = request.user.profile

    if friend_profile in user_profile.friends.all():
        user_profile.remove_friend(friend_profile)
        messages.success(request, f'{friend_profile.user.username} a été retiré de vos amis.')
    else:
        messages.error(request, 'Cet utilisateur n\'est pas dans votre liste d\'amis.')

    return redirect('view_friends')


def send_notification_email(subject, message, recipient_list):
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, recipient_list)

@login_required
def modifier_sortie(request, sortie_id):
    sortie = get_object_or_404(SortieProposee, id=sortie_id)
    if request.method == 'POST':
        form = SortieProposeeForm(request.POST, instance=sortie)
        if form.is_valid():
            old_date = sortie.date
            old_lieu = sortie.lieu

            sortie = form.save()

            # Si la date ou le lieu a changé, envoyer un email de notification
            if old_date != sortie.date or old_lieu != sortie.lieu:
                participants = sortie.participants.all()
                for participant in participants:
                    subject = 'Modification de la sortie'
                    message = f'La sortie "{sortie.nom}" a été modifiée.\nNouvelle date : {sortie.date}\nNouveau lieu : {sortie.lieu}'
                    recipient_list = [participant.email]
                    send_notification_email(subject, message, recipient_list)

            messages.success(request, 'La sortie a été modifiée avec succès.')
            return redirect('groupe_detail', group_id=sortie.groupe.id)
    else:
        form = SortieProposeeForm(instance=sortie)

    return render(request, 'sorties/modifier_sortie.html', {'form': form, 'sortie': sortie})

@login_required
def supprimer_sortie(request, sortie_id):
    sortie = get_object_or_404(SortieProposee, id=sortie_id)
    if request.user == sortie.createur or request.user == sortie.groupe.administrateur:
        participants = sortie.participants.all()
        participant_emails = [participant.email for participant in participants]

        sortie.delete()

        # Envoyer un e-mail de notification à tous les participants
        subject = 'Annulation de la sortie'
        message = f'La sortie "{sortie.nom}" a été annulée.'
        send_notification_email(subject, message, participant_emails)

        messages.success(request, 'La sortie a été supprimée avec succès.')
        return redirect('groupe_detail', group_id=sortie.groupe.id)
    else:
        messages.error(request, 'Vous n\'êtes pas autorisé à supprimer cette sortie.')
        return redirect('groupe_detail', group_id=sortie.groupe.id)

@login_required
def modifier_proposition(request, proposition_id):
    proposition = get_object_or_404(PropositionSortie, id=proposition_id, createur=request.user)
    if request.method == 'POST':
        form = PropositionSortieForm(request.POST, instance=proposition)
        if form.is_valid():
            form.save()
            messages.success(request, 'La proposition a été modifiée avec succès.')
            return redirect('groupe_detail', group_id=proposition.groupe.id)
    else:
        form = PropositionSortieForm(instance=proposition)
    return render(request, 'sorties/modifier_proposition.html', {'form': form, 'proposition': proposition})

@login_required
def supprimer_proposition(request, proposition_id):
    proposition = get_object_or_404(PropositionSortie, id=proposition_id)
    if request.user == proposition.createur:
        proposition.delete()
        messages.success(request, 'La proposition a été supprimée avec succès.')
    else:
        messages.error(request, 'Vous n\'avez pas la permission de supprimer cette proposition.')
    return redirect('groupe_detail', group_id=proposition.groupe.id)


@login_required
def mes_evenements(request):
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        action = request.POST.get('action')
        event = get_object_or_404(SortieProposee, id=event_id)

        if action == 'participer':
            participation, created = Participation.objects.get_or_create(sortie=event, membre=request.user)
            participation.vient = True
            participation.save()
            messages.success(request, 'Vous participez à cet événement.')
        elif action == 'annuler':
            Participation.objects.filter(sortie=event, membre=request.user).delete()
            messages.success(request, 'Vous avez annulé votre participation.')

        return redirect('mes_evenements')

    user_groups = GroupeAmis.objects.filter(membres=request.user)
    all_events = SortieProposee.objects.filter(groupe__in=user_groups).select_related('groupe')
    user_participations = Participation.objects.filter(membre=request.user, vient=True).select_related('sortie')

    participation_status = {participation.sortie.id: 'Je participe' for participation in user_participations}
    user_events = [participation.sortie for participation in user_participations]

    now = timezone.now()
    # Séparez les événements futurs et passés
    upcoming_events = [event for event in all_events if event.date >= now]
    past_events = [event for event in all_events if event.date < now]

    user_events_serialized = json.dumps([
        {
            'nom': event.nom,
            'date': event.date.isoformat(),
            'lieu': event.lieu,
            'groupe': event.groupe.nom
        } for event in upcoming_events if event.id in participation_status
    ], cls=DjangoJSONEncoder)

    context = {
        'all_events': upcoming_events,
        'participation_status': participation_status,
        'user_events': user_events_serialized,
        'past_events': past_events,
    }
    return render(request, 'sorties/mes_evenements.html', context)

@login_required
def toggle_participation(request, event_id):
    event = get_object_or_404(SortieProposee, id=event_id)
    participation, created = Participation.objects.get_or_create(membre=request.user, sortie=event)

    if participation.vient:
        participation.vient = False
        messages.success(request, f'Vous avez annulé votre participation à {event.nom}.')
    else:
        participation.vient = True
        messages.success(request, f'Vous participez maintenant à {event.nom}.')

    participation.save()
    return redirect('mes_evenements')

@login_required
def annuler_participation(request, participation_id):
    participation = get_object_or_404(Participation, id=participation_id, membre=request.user)
    if request.method == 'POST':
        participation.vient = False
        participation.save()
        messages.success(request, 'Vous avez annulé votre participation à cet événement.')
    return redirect('mes_evenements')

@login_required
def ajouter_membre(request, group_id):
    groupe = get_object_or_404(GroupeAmis, id=group_id)
    if request.user != groupe.administrateur:
        messages.error(request, "Vous n'êtes pas autorisé à ajouter des membres à ce groupe.")
        return redirect('groupe_detail', group_id=group_id)

    profile = Profile.objects.get(user=request.user)
    friends = profile.friends.exclude(id__in=groupe.membres.values_list('id', flat=True))

    if request.method == 'POST':
        selected_user_ids = request.POST.get('selected_users').split(',')
        for user_id in selected_user_ids:
            user = User.objects.get(id=user_id)
            groupe.membres.add(user)
        messages.success(request, "Les membres sélectionnés ont été ajoutés au groupe.")
        return redirect('groupe_detail', group_id=group_id)

    return render(request, 'sorties/ajouter_membre.html', {'groupe': groupe, 'friends': friends})

@login_required
def quitter_groupe(request, group_id):
    groupe = get_object_or_404(GroupeAmis, id=group_id)
    if request.user in groupe.membres.all():
        groupe.membres.remove(request.user)
        messages.success(request, "Vous avez quitté le groupe.")
    else:
        messages.error(request, "Vous ne faites pas partie de ce groupe.")
    return redirect('liste_groupes')

@login_required
def supprimer_membre(request, group_id, user_id):
    groupe = get_object_or_404(GroupeAmis, id=group_id)
    if request.user != groupe.administrateur:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer des membres de ce groupe.")
        return redirect('groupe_detail', group_id=group_id)

    membre = get_object_or_404(User, id=user_id)
    if membre == groupe.administrateur:
        messages.error(request, "Vous ne pouvez pas vous supprimer en tant qu'administrateur du groupe.")
    else:
        groupe.membres.remove(membre)
        messages.success(request, f'{membre.username} a été supprimé du groupe.')
    
    return redirect('groupe_detail', group_id=group_id)

@login_required
def view_profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    # Calculer le Hall of Fame
    participations = Participation.objects.filter(membre=profile_user, vient=True)
    friends_counter = {}
    for participation in participations:
        for friend in participation.sortie.participants.all():
            if friend != profile_user:
                if friend not in friends_counter:
                    friends_counter[friend] = 0
                friends_counter[friend] += 1

    top_friends = sorted(friends_counter.items(), key=lambda x: x[1], reverse=True)[:3]

    context = {
        'profile_user': profile_user,
        'top_friends': top_friends
    }

    return render(request, 'sorties/view_profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('view_profile', username=request.user.username)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    return render(request, 'sorties/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def proposer_sortie(request, group_id):
    groupe = get_object_or_404(GroupeAmis, id=group_id)
    if request.method == 'POST':
        form = SortieProposeeForm(request.POST)
        if form.is_valid():
            sortie = form.save(commit=False)
            sortie.groupe = groupe
            sortie.createur = request.user
            sortie.save()
            return redirect('groupe_detail', group_id=group_id)
    else:
        form = SortieProposeeForm()
    return render(request, 'sorties/proposer_sortie.html', {'form': form, 'groupe': groupe})

@login_required
def proposer_proposition(request, group_id):
    groupe = get_object_or_404(GroupeAmis, id=group_id)
    if request.method == 'POST':
        form = PropositionSortieForm(request.POST)
        if form.is_valid():
            proposition = form.save(commit=False)
            proposition.groupe = groupe
            proposition.createur = request.user
            proposition.save()
            
            dates = []
            for date_field in ['date_1', 'date_2', 'date_3']:
                date_value = form.cleaned_data[date_field]
                if date_value:
                    dates.append(DateProposee(proposition=proposition, date=date_value))

            DateProposee.objects.bulk_create(dates)
            
            messages.success(request, 'Proposition de sortie créée avec succès.')
            return redirect('groupe_detail', group_id=group_id)
    else:
        form = PropositionSortieForm()
    return render(request, 'sorties/proposer_proposition.html', {'form': form, 'groupe': groupe})


@login_required
def sortie_detail(request, sortie_id):
    sortie = get_object_or_404(SortieProposee, id=sortie_id)
    return render(request, 'sorties/sortie_detail.html', {'sortie': sortie})
    
@login_required
def groupe_detail(request, group_id):
    groupe = get_object_or_404(GroupeAmis, id=group_id)
    sorties = SortieProposee.objects.filter(groupe=groupe)
    propositions = PropositionSortie.objects.filter(groupe=groupe)

    if request.method == 'POST':
        if 'proposition_id' in request.POST:
            # Traiter le formulaire de vote pour les propositions de sorties
            proposition_id = request.POST.get('proposition_id')
            proposition = get_object_or_404(PropositionSortie, id=proposition_id)
            print(f"Traitement de la proposition: {proposition_id}")

            # Récupérer la date sélectionnée
            date_id = request.POST.get(f'vote_{proposition_id}')
            if date_id:
                date_proposee = get_object_or_404(DateProposee, id=date_id)
                print(f"Vote trouvé pour la date: {date_proposee.id}")

                # Supprimer les votes précédents de l'utilisateur pour cette proposition
                Vote.objects.filter(utilisateur=request.user, date_proposee__proposition=proposition).delete()

                # Créer le nouveau vote
                vote = Vote.objects.create(
                    utilisateur=request.user,
                    date_proposee=date_proposee,
                    vote=True
                )
                print(f"Nouveau vote créé: {vote.id} pour la date {date_proposee.id}")

                messages.success(request, 'Votre vote a été enregistré.')
            else:
                print("Aucune date sélectionnée pour le vote.")
                messages.error(request, 'Veuillez sélectionner une date avant de voter.')
            
            return redirect('groupe_detail', group_id=group_id)

        elif 'form_id' in request.POST:
            # Traiter le formulaire de participation aux sorties proposées
            sortie_id = request.POST.get('form_id')
            vient = request.POST.get('vient') == 'True'
            sortie = get_object_or_404(SortieProposee, id=sortie_id)

            if vient:
                participation, created = Participation.objects.get_or_create(sortie=sortie, membre=request.user)
                participation.vient = True
                participation.save()
            else:
                Participation.objects.filter(sortie=sortie, membre=request.user).delete()
            messages.success(request, 'Votre participation a été mise à jour.')
            return redirect('groupe_detail', group_id=group_id)

    return render(request, 'sorties/groupe_detail.html', {
        'groupe': groupe,
        'sorties': sorties,
        'propositions': propositions
    })




@login_required
def finaliser_sortie(request, proposition_id):
    proposition = get_object_or_404(PropositionSortie, id=proposition_id)
    dates_proposees = proposition.dates.all()

    if not dates_proposees:
        messages.error(request, 'Aucune date proposée pour cette sortie.')
        return redirect('groupe_detail', group_id=proposition.groupe.id)

    # Ajout de messages de débogage
    print("Dates proposées :", dates_proposees)

    date_finale = max(dates_proposees, key=lambda d: d.vote_set.filter(vote=True).count(), default=None)

    # Vérifiez que des votes ont été enregistrés
    if not date_finale:
        messages.error(request, 'Aucun vote enregistré pour cette sortie.')
        return redirect('groupe_detail', group_id=proposition.groupe.id)

    print("Date finale :", date_finale)

    sortie = SortieProposee.objects.create(
        groupe=proposition.groupe,
        nom=proposition.nom,
        description=proposition.description,
        date=date_finale.date,
        lieu=proposition.lieu,
        createur=proposition.createur
    )

    messages.success(request, 'La sortie a été finalisée avec la date ayant le plus de votes.')
    return redirect('groupe_detail', group_id=proposition.groupe.id)

@login_required
def repondre_sortie(request, sortie_id):
    sortie = get_object_or_404(SortieProposee, id=sortie_id)
    if request.method == 'POST':
        form = ParticipationForm(request.POST)
        if form.is_valid():
            participation = form.save(commit=False)
            participation.sortie = sortie
            participation.membre = request.user
            participation.save()
            return redirect('groupe_detail', group_id=sortie.groupe.id)
    else:
        form = ParticipationForm()
    return render(request, 'sorties/repondre_sortie.html', {'form': form, 'sortie': sortie})


@login_required
def creer_groupe(request):
    if request.method == 'POST':
        form = GroupeAmisForm(request.POST, user=request.user)
        if form.is_valid():
            groupe = form.save(commit=False)
            groupe.createur = request.user
            groupe.administrateur = request.user
            groupe.save()
            form.save_m2m()
            # Assurer que le créateur est membre après save_m2m()
            if request.user not in groupe.membres.all():
                groupe.membres.add(request.user)
            messages.success(request, 'Le groupe a été créé avec succès.')
            print(f"Groupe créé: {groupe.nom}, Membres: {[m.username for m in groupe.membres.all()]}")
            return redirect('liste_groupes')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = GroupeAmisForm(user=request.user)
    return render(request, 'sorties/creer_groupe.html', {'form': form})

@login_required
def liste_groupes(request):
    query = request.GET.get('q')
    if query:
        groupes = GroupeAmis.objects.filter(nom__icontains=query, membres=request.user)
    else:
        groupes = GroupeAmis.objects.filter(membres=request.user)

    return render(request, 'sorties/liste_groupes.html', {'groupes': groupes})

@login_required
def search_users(request):
    query = request.GET.get('q')
    if query:
        users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query)).distinct()
    else:
        users = []
    return render(request, 'sorties/search_users.html', {'users': users})

@login_required
def send_friend_request(request, user_id):
    if request.user.id == user_id:
        messages.error(request, "Vous ne pouvez pas vous ajouter vous-même en ami.")
        return redirect('search_users')
    
    user = get_object_or_404(User, id=user_id)
    
    # Vérifier si une demande d'ami existe déjà
    friend_requests_sent = FriendRequest.objects.filter(from_user=request.user, to_user=user).exists()
    friend_requests_received = FriendRequest.objects.filter(from_user=user, to_user=request.user).exists()
    already_friends = request.user.profile.friends.filter(id=user.profile.id).exists()
    
    if friend_requests_sent or friend_requests_received:
        messages.info(request, f'Une demande d\'ami est déjà en attente avec {user.username}.')
    elif already_friends:
        messages.info(request, f'Vous êtes déjà amis avec {user.username}.')
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=user)
        messages.success(request, f'Demande d\'ami envoyée à {user.username}.')
    
    return redirect('search_users')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    if friend_request.to_user == request.user:
        friend_request.to_user.profile.add_friend(friend_request.from_user.profile)
        friend_request.delete()
        messages.success(request, f'Vous avez accepté la demande d\'ami de {friend_request.from_user.username}.')
    return redirect('view_friends')

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    if friend_request.to_user == request.user:
        friend_request.delete()
        messages.info(request, f'Vous avez rejeté la demande d\'ami de {friend_request.from_user.username}.')
    return redirect('view_friends')

@login_required
def view_friends(request):
    friends = request.user.profile.friends.all()
    friend_requests = FriendRequest.objects.filter(to_user=request.user)
    pending_requests_count = friend_requests.count()
    
    context = {
        'friends': friends,
        'friend_requests': friend_requests,
        'pending_requests_count': pending_requests_count
    }
    return render(request, 'sorties/view_friends.html', context)
    

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Votre compte a été créé avec succès !')
            return redirect('liste_groupes')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'sorties/register.html', {'form': form})

def accueil(request):
    return render(request, 'sorties/accueil.html')


def logout_view(request):
    logout(request)
    return redirect('accueil')


