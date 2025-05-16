from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from backend.models import Vehicle, DriverProfile
import re
from django.utils import timezone

class RegisterVehicleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể đăng ký phương tiện.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
        except DriverProfile.DoesNotExist:
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        license_plate = request.data.get('license_plate')
        brand = request.data.get('brand')
        model = request.data.get('model')
        year = request.data.get('year')

        # Validate input
        if not all([license_plate, brand, model, year]):
            return Response({'error': 'Vui lòng điền đầy đủ thông tin phương tiện.'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r'^\d{2}[A-Z]{1,2}-\d{4,5}$', license_plate):
            return Response({'error': 'Biển số xe không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year = int(year)
            if year < 1900 or year > timezone.now().year:
                return Response({'error': 'Năm sản xuất không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Năm sản xuất phải là số.'}, status=status.HTTP_400_BAD_REQUEST)

        if Vehicle.objects.filter(license_plate=license_plate).exists():
            return Response({'error': 'Biển số xe đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        if Vehicle.objects.filter(driver=driver_profile).exists():
            return Response({'error': 'Bạn đã đăng ký một phương tiện.'}, status=status.HTTP_400_BAD_REQUEST)

        vehicle = Vehicle.objects.create(
            driver=driver_profile,
            vehicle_type='bike',
            license_plate=license_plate,
            brand=brand,
            model=model,
            year=year
        )

        return Response({
            'message': 'Đăng ký phương tiện thành công!',
            'vehicle': {
                'license_plate': vehicle.license_plate,
                'brand': vehicle.brand,
                'model': vehicle.model,
                'year': vehicle.year
            }
        }, status=status.HTTP_201_CREATED)

class DeleteVehicleView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể xóa phương tiện.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
            vehicle = driver_profile.vehicle
            vehicle.delete()
            return Response({'message': 'Xóa phương tiện thành công!'}, status=status.HTTP_200_OK)
        except (DriverProfile.DoesNotExist, Vehicle.DoesNotExist):
            return Response({'error': 'Không tìm thấy phương tiện.'}, status=status.HTTP_404_NOT_FOUND)
