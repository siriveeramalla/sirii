import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from varuni.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suhitha.settings')
django.setup()
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})
