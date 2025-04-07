from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from .models import LoggedInUser

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    session_key = request.session.session_key

    existing = LoggedInUser.objects.filter(user=user)
    if existing.exists():
        existing_session_key = existing[0].session_key
        Session.objects.filter(session_key=existing_session_key).delete()
        existing.delete()

    LoggedInUser.objects.create(user=user, session_key=session_key)

@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    LoggedInUser.objects.filter(user=user).delete()
