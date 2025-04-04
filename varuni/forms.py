from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Room
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class RoomForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)  # Hide password input

    class Meta:
        model = Room
        fields = ["name", "password"]
