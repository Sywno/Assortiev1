from django import forms
from .models import GroupeAmis, SortieProposee, Participation, Profile, PropositionSortie, DateProposee
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

class GroupeAmisForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(GroupeAmisForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['membres'].queryset = User.objects.filter(profile__in=user.profile.friends.all())

    class Meta:
        model = GroupeAmis
        fields = ['nom', 'membres']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'membres': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
        }

class SortieProposeeForm(forms.ModelForm):
    class Meta:
        model = SortieProposee
        fields = ['nom', 'description', 'date', 'lieu']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("La date ne peut pas être antérieure à la date actuelle.")
        return date

class DateProposeeForm(forms.ModelForm):
    class Meta:
        model = DateProposee
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
        }

class PropositionSortieForm(forms.ModelForm):
    date_1 = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}), required=False)
    date_2 = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}), required=False)
    date_3 = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}), required=False)

    class Meta:
        model = PropositionSortie
        fields = ['nom', 'description', 'lieu']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ParticipationForm(forms.ModelForm):
    class Meta:
        model = Participation
        fields = ['vient']
        widgets = {
            'vient': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['photo', 'other_profile_field']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'other_profile_field': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'photo')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            if self.cleaned_data['photo']:
                profile.photo = self.cleaned_data['photo']
            else:
                profile.photo = 'profile_pics/default_profile.jpg'
            profile.save()
        return user
    
class AddMemberForm(forms.Form):
    membre = forms.ModelChoiceField(queryset=User.objects.all(), label="Ajouter un membre", widget=forms.Select(attrs={'class': 'form-control'}))
