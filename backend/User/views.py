from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.http import JsonResponse
from backend.models import User, DriverProfile, Vehicle
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError

# UserView
class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        phone = request.data.get("phone")
        role = request.data.get("role", "customer")

        if not all([email, password, phone, username]):
            return Response(
                {"error": "Email, password, phone, and username are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                phone=phone,
                role=role
            )
            refresh = RefreshToken.for_user(user)
            return Response({
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if "email" in str(e).lower() or "phone" in str(e).lower():
                return Response(
                    {"error": "Email or phone already exists"},
                    status=status.HTTP_409_CONFLICT
                )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)

        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    def post(self, request):
        response = JsonResponse({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Bảo vệ bằng JWT

    def get(self, request):
        user = request.user  # Lấy user từ Access Token

        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
        }

        # Nếu user là tài xế, lấy thêm thông tin từ `DriverProfile`
        if user.role == "driver":
            print(user.role)
            try:
                driver_profile = user.driverprofile
                profile_data["license_number"] = driver_profile.license_number
                profile_data["is_available"] = driver_profile.is_available
                profile_data["rating"] = driver_profile.rating
            except DriverProfile.DoesNotExist:
                return Response({"error": "Driver profile not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(profile_data)

class RegisterDriverView(APIView):
    permission_classes = [IsAuthenticated]  # Bảo vệ bằng JWT

    def post(self, request):
        user = request.user

        if user.role == "driver":
            return Response({"error": "You are already a driver"}, status=status.HTTP_400_BAD_REQUEST)

        license_number = request.data.get("license_number")
        if not license_number:
            return Response({"error": "License number is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.role = "driver"
        user.save()
        
        DriverProfile.objects.create(
            user = user,
            license_number = license_number
        )

        return Response({
            "message": "Successfully registered as a driver",
            "role": user.role,
            "license_number": license_number
        }, status=status.HTTP_200_OK)
