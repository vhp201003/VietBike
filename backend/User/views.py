from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from backend.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
import os

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        phone = request.data.get('phone')
        password = request.data.get('password')

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(phone=phone).exists():
            return Response({'error': 'Số điện thoại đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            password=password,
            role='customer'
        )
        Token.objects.create(user=user)

        return Response({
            'message': 'Đăng ký thành công! Vui lòng đăng nhập.',
            'user': {'username': username, 'email': email, 'phone': phone}
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'access_token': token.key,
                'username': user.username,
                'role': user.role,
                'message': 'Đăng nhập thành công!'
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Email hoặc mật khẩu không đúng.'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response({'message': 'Đăng xuất thành công!'}, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'role': user.role
        }
        return Response(data)

    def put(self, request):
        user = request.user
        data = request.data

        # Cập nhật thông tin người dùng
        if 'username' in data:
            user.username = data['username']
        if 'email' in data and data['email'] != user.email:
            if User.objects.filter(email=data['email']).exists():
                return Response({'error': 'Email đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
            user.email = data['email']
        if 'phone' in data and data['phone'] != user.phone:
            if User.objects.filter(phone=data['phone']).exists():
                return Response({'error': 'Số điện thoại đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
            user.phone = data['phone']
        if 'new_password' in data and 'old_password' in data:
            if user.check_password(data['old_password']):
                user.set_password(data['new_password'])
            else:
                return Response({'error': 'Mật khẩu cũ không đúng.'}, status=status.HTTP_400_BAD_REQUEST)
        if 'profile_picture' in request.FILES:
            if user.profile_picture:
                os.remove(user.profile_picture.path)
            user.profile_picture = request.FILES['profile_picture']
        if data.get('remove_image') == 'true' and user.profile_picture:
            os.remove(user.profile_picture.path)
            user.profile_picture = None
        user.save()

        return Response({
            'message': 'Cập nhật hồ sơ thành công!',
            'profile': {
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'role': user.role
            }
        }, status=status.HTTP_200_OK)
