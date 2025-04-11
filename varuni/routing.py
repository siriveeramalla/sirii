from django.urls import re_path
from varuni import consumers  # Adjust this if app name is different

websocket_urlpatterns = [
    re_path(r'ws/document/(?P<room_id>\d+)/$', consumers.DocumentConsumer.as_asgi()),
]
