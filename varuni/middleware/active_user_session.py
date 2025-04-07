from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

class OneSessionPerUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            current_session_key = request.session.session_key
            now = timezone.now()
            all_sessions = Session.objects.filter(expire_date__gte=now)

            for session in all_sessions:
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(request.user.id):
                    if session.session_key != current_session_key:
                        logout(request)
                        break
