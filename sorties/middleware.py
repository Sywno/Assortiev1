from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Middleware qui redirige les utilisateurs non connectés vers la page d'accueil.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Liste des chemins d'URL à autoriser pour les utilisateurs non authentifiés
        allowed_urls = [
            reverse('login'),
            reverse('register'),
            reverse('accueil'),
            '/admin/',
            '/accounts/google/login/',
            '/accounts/google/login/callback/'
        ]

        if not request.user.is_authenticated and request.path not in allowed_urls:
            return redirect('accueil')
        response = self.get_response(request)
        return response
