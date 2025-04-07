from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.models import DriverProfile, Vehicle
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError


class RegisterVehicleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # Kiểm tra xem user có phải là driver hay không
        print(user.role)
        if user.role != 'driver':
            return Response(
                {"error": "Tài khoản này chưa đăng ký role 'driver'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lấy driver profile của user
        try:
            driver_profile = user.driverprofile
        except DriverProfile.DoesNotExist:
            return Response({"error": "Không tìm thấy DriverProfile"}, status=status.HTTP_404_NOT_FOUND)

        vehicle_type = request.data.get('vehicle_type')
        license_plate = request.data.get('license_plate')
        brand = request.data.get('brand')
        model = request.data.get('model')
        year = request.data.get('year')

        if not all([vehicle_type, license_plate, brand, model, year]):
            return Response(
                {"error": "Vui lòng truyền đủ các trường: vehicle_type, license_plate, brand, model, year"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Do quan hệ OneToOne, một driver chỉ được gắn 1 vehicle
            vehicle = Vehicle.objects.create(
                driver=driver_profile,
                vehicle_type=vehicle_type,
                license_plate=license_plate,
                brand=brand,
                model=model,
                year=year
            )
            return Response({"message": "Đăng ký xe thành công!"}, status=status.HTTP_201_CREATED)

        except IntegrityError:
            # Thường gặp lỗi nếu license_plate đã tồn tại hoặc driver đã có vehicle
            return Response({"error": "Thông tin xe hoặc tài xế bị trùng lặp (ví dụ: license_plate đã tồn tại)"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DeleteVehicleView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        # Kiểm tra role phải là driver
        if user.role != 'driver':
            return Response({"error": "Tài khoản này chưa đăng ký role 'driver'"}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy driver profile
        try:
            driver_profile = user.driverprofile
        except DriverProfile.DoesNotExist:
            return Response({"error": "Không tìm thấy DriverProfile"}, status=status.HTTP_404_NOT_FOUND)

        # Do quan hệ OneToOneField, nếu chưa có vehicle, sẽ bắn lỗi Vehicle.DoesNotExist
        try:
            vehicle = driver_profile.vehicle
        except Vehicle.DoesNotExist:
            return Response({"error": "Bạn chưa đăng ký bất kỳ phương tiện nào"}, status=status.HTTP_404_NOT_FOUND)

        # Xóa vehicle
        vehicle.delete()
        return Response({"message": "Xóa vehicle thành công!"}, status=status.HTTP_200_OK)