import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suhitha.settings')
django.setup()  # 👈 ADD THIS LINE BEFORE importing varuni.routing

import varuni.routing  # Now it's safe to import

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            varuni.routing.websocket_urlpatterns
        )
    ),
})

