from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import SortieProposee, Participation

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(pre_save, sender=SortieProposee)
def notify_participants_on_change(sender, instance, **kwargs):
    if instance.pk:
        old_instance = SortieProposee.objects.get(pk=instance.pk)
        if old_instance.date != instance.date or old_instance.lieu != instance.lieu:
            participants = Participation.objects.filter(sortie=instance, vient=True).select_related('membre')
            for participation in participants:
                user = participation.membre
                subject = 'Modification de la sortie : {}'.format(instance.nom)
                html_message = render_to_string('emails/sortie_modification.html', {
                    'user': user,
                    'sortie': instance,
                    'old_date': old_instance.date,
                    'new_date': instance.date,
                    'old_lieu': old_instance.lieu,
                    'new_lieu': instance.lieu
                })
                plain_message = strip_tags(html_message)
                from_email = 'Assortie8@outlook.com'
                to = user.email

                send_mail(subject, plain_message, from_email, [to], html_message=html_message)