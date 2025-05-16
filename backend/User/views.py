from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
import logging

User = get_user_model()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        phone = request.data.get('phone')
        password = request.data.get('password')
        
        if not all([username, email, phone, password]):
            return Response({'error': 'Vui lòng cung cấp đầy đủ thông tin.'}, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'message': 'Đăng ký thành công!',
            'user': {
                'username': user.username,
                'email': user.email,
                'phone': user.phone
            }
        }, status=status.HTTP_201_CREATED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            from rest_framework_simplejwt.tokens import RefreshToken
            
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({'message': 'Đăng xuất thành công!'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'user': {  # Thêm key 'user' để khớp với frontend
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'created_at': user.created_at.isoformat()
            }
        }, status=200)

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        username = request.data.get('username', user.username)
        phone = request.data.get('phone', user.phone)
        email = request.data.get('email', user.email)
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        remove_image = request.data.get('remove_image')

        logger.debug(f"Request data: {request.data}")
        logger.debug(f"Request FILES: {request.FILES}")

        if email != user.email and User.objects.filter(email=email).exists():
            return Response({'error': 'Email đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        if phone != user.phone and User.objects.filter(phone=phone).exists():
            return Response({'error': 'Số điện thoại đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)

        user.username = username
        user.phone = phone
        user.email = email

        if old_password and new_password:
            if not user.check_password(old_password):
                return Response({'error': 'Mật khẩu cũ không đúng.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)

        if remove_image == 'true' and user.profile_picture:
            if default_storage.exists(user.profile_picture.name):
                default_storage.delete(user.profile_picture.name)
            user.profile_picture = None
        elif 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            logger.debug(f"Received file: {profile_picture.name}, size: {profile_picture.size}")
            if profile_picture.size > 5 * 1024 * 1024:
                return Response({'error': 'File ảnh quá lớn. Vui lòng chọn file nhỏ hơn 5MB.'}, status=400)
            if user.profile_picture and default_storage.exists(user.profile_picture.name):
                default_storage.delete(user.profile_picture.name)
            try:
                user.profile_picture = profile_picture
                user.save()
                logger.debug(f"File saved at: {user.profile_picture.path}")
            except Exception as e:
                logger.error(f"Error saving file: {str(e)}")
                return Response({'error': f'Lỗi lưu file: {str(e)}'}, status=400)
        else:
            logger.warning("No profile_picture in request.FILES")

        user.save()

        return Response({
            'message': 'Cập nhật hồ sơ thành công!',
            'user': {
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'created_at': user.created_at.isoformat()
            }
        }, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not all([old_password, new_password]):
            return Response({'error': 'Vui lòng cung cấp mật khẩu cũ và mới.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(old_password):
            return Response({'error': 'Mật khẩu cũ không đúng.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Đổi mật khẩu thành công!'}, status=status.HTTP_200_OK)
