from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from sorties import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.accueil, name='accueil'),  # Ajoutez cette ligne
    path('sorties/', include('sorties.urls')),
    path('accounts/', include('allauth.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)