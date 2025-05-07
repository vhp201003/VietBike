import requests
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class AutoRefreshTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')

        if access_token and refresh_token:
            try:
                JWTAuthentication().get_validated_token(access_token)
            except InvalidToken:
                try:
                    response = requests.post(
                        f'{settings.BACKEND_API_URL}/token/refresh/',
                        data={'refresh': refresh_token}
                    )
                    if response.status_code == 200:
                        new_tokens = response.json()
                        request.session['access_token'] = new_tokens['access']
                        if 'refresh' in new_tokens:
                            request.session['refresh_token'] = new_tokens['refresh']
                    else:
                        request.session.flush()
                except requests.RequestException:
                    request.session.flush()

        response = self.get_response(request)
        return response
