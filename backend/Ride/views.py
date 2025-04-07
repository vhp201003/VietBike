from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from backend.models import Ride, DriverProfile, RideLocation


# 1. Customer tạo yêu cầu ride
class RequestRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Endpoint: POST /api/rides/request/
        Chỉ cho phép user role='customer' tạo chuyến đi
        """
        if request.user.role != "customer":
            return Response(
                {"error": "Chức năng này chỉ dành cho customer"},
                status=status.HTTP_403_FORBIDDEN
            )

        start_location = request.data.get("start_location")
        end_location = request.data.get("end_location")
        
        if not start_location or not end_location:
            return Response(
                {"error": "Thiếu start_location hoặc end_location"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Tạo ride mới
        ride = Ride.objects.create(
            user=request.user,
            start_location=start_location,
            end_location=end_location,
            status='requested'  # Theo STATUS_CHOICES = ('requested', 'accepted', 'completed')
        )

        return Response(
            {
                "message": "Tạo yêu cầu chuyến đi thành công",
                "ride_id": ride.id,
                "start_location": ride.start_location,
                "end_location": ride.end_location,
                "status": ride.status,
            },
            status=status.HTTP_201_CREATED
        )

# 2. Lấy danh sách các ride đang ở trạng thái requested (chưa có tài xế)
class ListRequestedRidesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Endpoint: GET /api/rides/requested/
        Chỉ cho phép user role='driver' lấy danh sách các chuyến chưa có tài xế
        """
        if request.user.role != 'driver':
            return Response(
                {"error": "Chức năng này chỉ dành cho tài xế"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Lọc Ride đang 'requested' và chưa có driver
        rides = Ride.objects.filter(status='requested', driver__isnull=True)
        data = []
        for ride in rides:
            data.append({
                "ride_id": ride.id,
                "start_location": ride.start_location,
                "end_location": ride.end_location,
                "user_id": ride.user.id,  # Customer
                "requested_at": ride.requested_at,
            })

        return Response(data, status=status.HTTP_200_OK)

# 3. Tài xế nhận chuyến
class AcceptRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        """
        Endpoint: POST /api/rides/accept/<ride_id>/
        Tài xế nhận chuyến -> ride.status='accepted', ride.driver = driverProfile
        """
        if request.user.role != "driver":
            return Response(
                {"error": "Chức năng này chỉ dành cho tài xế"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Lấy Ride và kiểm tra trạng thái
        ride = get_object_or_404(Ride, id=ride_id)

        if ride.status != 'requested' or ride.driver is not None:
            return Response(
                {"error": "Chuyến này không thể nhận (đã có tài xế hoặc không còn requested)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lấy driverProfile của user hiện tại
        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
        except DriverProfile.DoesNotExist:
            return Response({"error": "Bạn chưa có DriverProfile"}, status=status.HTTP_404_NOT_FOUND)

        # Gán cho ride
        ride.driver = driver_profile
        ride.status = 'accepted'
        ride.save()

        return Response(
            {
                "message": "Nhận chuyến thành công",
                "ride_id": ride.id,
                "status": ride.status,
                "driver": ride.driver.user.email,
            },
            status=status.HTTP_200_OK
        )

# 4. Cập nhật trạng thái chuyến (VD: 'completed')
class UpdateRideStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        """
        Endpoint: POST /api/rides/update-status/<ride_id>/
        Tài xế cập nhật trạng thái chuyến (hoặc logic thêm, tùy dự án)
        """
        ride = get_object_or_404(Ride, id=ride_id)
        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Thiếu status mới"}, status=status.HTTP_400_BAD_REQUEST)

        # Chỉ cho phép tài xế cập nhật, hoặc custom logic
        if request.user.role != 'driver':
            return Response({"error": "Chỉ tài xế được cập nhật"}, status=status.HTTP_403_FORBIDDEN)

        # Kiểm tra ride.driver có phải driverProfile của user hay không
        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
        except DriverProfile.DoesNotExist:
            return Response({"error": "Bạn chưa có DriverProfile"}, status=status.HTTP_404_NOT_FOUND)

        if ride.driver != driver_profile:
            return Response({"error": "Bạn không phải tài xế của chuyến này"}, status=status.HTTP_403_FORBIDDEN)

        # Cập nhật
        if new_status not in ['accepted', 'completed']:
            return Response({"error": "Trạng thái không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)

        ride.status = new_status

        if new_status == 'completed':
            ride.completed_at = timezone.now()

        ride.save()

        return Response({
            "message": "Cập nhật trạng thái thành công",
            "ride_id": ride.id,
            "status": ride.status
        }, status=status.HTTP_200_OK)

# 5. Theo dõi vị trí tài xế (nếu có lưu trong RideLocation)
class TrackDriverLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ride_id):
        """
        Endpoint: GET /api/rides/track-driver/<ride_id>/
        Customer (chủ chuyến) hoặc chính tài xế có thể xem lịch sử/tọa độ hiện tại
        """
        ride = get_object_or_404(Ride, id=ride_id)

        # Cho phép customer (ride.user) hoặc driver (ride.driver) xem
        if request.user != ride.user:
            # So sánh user với driverProfile.user
            # ride.driver là DriverProfile -> ride.driver.user là User
            if not (ride.driver and request.user == ride.driver.user):
                return Response({"error": "Bạn không có quyền xem vị trí chuyến này"}, status=status.HTTP_403_FORBIDDEN)

        # Lấy thông tin vị trí gần nhất (hoặc tất cả) từ RideLocation
        locations = RideLocation.objects.filter(ride=ride).order_by('-timestamp')
        if not locations.exists():
            return Response({"message": "Chưa có tọa độ nào"}, status=status.HTTP_404_NOT_FOUND)

        # Giả sử ta trả về vị trí mới nhất (hoặc danh sách)
        latest_location = locations.first()
        data = {
            "ride_id": ride.id,
            "driver_id": ride.driver.id if ride.driver else None,
            "latitude": latest_location.latitude,
            "longitude": latest_location.longitude,
            "timestamp": latest_location.timestamp,
        }
        return Response(data, status=status.HTTP_200_OK)
