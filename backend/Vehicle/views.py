from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from backend.models import Vehicle, DriverProfile
import logging
import re

logger = logging.getLogger(__name__)

class RegisterVehicleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'driver':
            return Response({"error": "Bạn phải là tài xế để đăng ký phương tiện"}, status=status.HTTP_403_FORBIDDEN)
        
        license_plate = request.data.get('license_plate')
        brand = request.data.get('brand')
        model = request.data.get('model')
        year = request.data.get('year')
        
        if not all([license_plate, brand, model, year]):
            return Response({"error": "Vui lòng điền đầy đủ thông tin"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not re.match(r'^\d{4}$', year):
            return Response({"error": "Năm sản xuất không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
        
        if Vehicle.objects.filter(license_plate=license_plate).exists():
            return Response({"error": "Biển số xe đã được sử dụng"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            driver_profile = DriverProfile.objects.get(user=user)
            if Vehicle.objects.filter(driver=driver_profile).exists():
                return Response({"error": "Tài xế đã có phương tiện"}, status=status.HTTP_400_BAD_REQUEST)
            vehicle = Vehicle.objects.create(
                driver=driver_profile,
                vehicle_type='bike',
                license_plate=license_plate,
                brand=brand,
                model=model,
                year=int(year)
            )
            logger.debug(f"Vehicle created: {vehicle.id}")
            return Response({"message": "Đăng ký phương tiện thành công"}, status=status.HTTP_201_CREATED)
        except DriverProfile.DoesNotExist:
            return Response({"error": "Hồ sơ tài xế không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating vehicle: {str(e)}")
            return Response({"error": f"Lỗi đăng ký phương tiện: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteVehicleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'driver':
            return Response({"error": "Bạn phải là tài xế để xóa phương tiện"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            driver_profile = DriverProfile.objects.get(user=user)
            vehicle = Vehicle.objects.get(driver=driver_profile)
            vehicle.delete()
            logger.debug(f"Vehicle deleted for driver: {driver_profile.id}")
            return Response({"message": "Xóa phương tiện thành công"}, status=status.HTTP_200_OK)
        except (DriverProfile.DoesNotExist, Vehicle.DoesNotExist):
            return Response({"error": "Phương tiện hoặc hồ sơ tài xế không tồn tại"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting vehicle: {str(e)}")
            return Response({"error": f"Lỗi xóa phương tiện: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
