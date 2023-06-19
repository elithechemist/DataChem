from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class AdminVerificationRequestForm(forms.Form):
    group_name = forms.CharField(label='Group Name', max_length=100)
    institution = forms.CharField(label='Institution', max_length=100)

class AddGroupMemberForm(forms.Form):
    username_or_email = forms.CharField()

class RemoveGroupMemberForm(forms.Form):
    username_or_email = forms.CharField()