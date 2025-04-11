"""
ASGI config for suhitha project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import varuni.routing  # Adjust based on your app name

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suhitha.settings')  # adjust if needed

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            varuni.routing.websocket_urlpatterns
        )
    ),
})

