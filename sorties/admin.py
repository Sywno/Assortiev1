from django.contrib import admin
from .models import Profile, FriendRequest, GroupeAmis, Message, SortieProposee, Participation, DateProposee, Vote, PropositionSortie

admin.site.register(Profile)
admin.site.register(FriendRequest)
admin.site.register(GroupeAmis)
admin.site.register(Message)
admin.site.register(SortieProposee)
admin.site.register(Participation)
admin.site.register(DateProposee)
admin.site.register(Vote)
admin.site.register(PropositionSortie)
