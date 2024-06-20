# sortie_project/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import sorties.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sortie_project.settings')

# Initialise Django
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            sorties.routing.websocket_urlpatterns
        )
    ),
})
