from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.http import JsonResponse

class AutoRefreshTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth = JWTAuthentication()
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        if access_token:
            try:
                validated_token = AccessToken(access_token)
                request.user = auth.get_user(validated_token)  # Token hợp lệ, tiếp tục request
                return None
            except Exception:
                if refresh_token:
                    try:
                        refresh = RefreshToken(refresh_token)
                        new_access_token = str(refresh.access_token)

                        response = JsonResponse({"access_token": new_access_token})
                        response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax", secure=True)
                        return response
                    except Exception:
                        return JsonResponse({"error": "Refresh token hết hạn, cần đăng nhập lại"}, status=401)

        return None
