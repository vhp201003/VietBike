from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .User.views import RegisterView, LogoutView, ProfileView, UpdateProfileView, ChangePasswordView
from .Ride.views import (
    RequestRideView, ListRequestedRidesView, AcceptRideView, UpdateRideStatusView,
    TrackDriverLocationView, RateRideView
)

app_name = 'backend'

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('users/logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update_profile'),
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),

    
    path('rides/request/', RequestRideView.as_view(), name='request_ride'),
    path('rides/requested/', ListRequestedRidesView.as_view(), name='list_requested_rides'),
    path('rides/<int:ride_id>/accept/', AcceptRideView.as_view(), name='accept_ride'),
    path('rides/<int:ride_id>/status/', UpdateRideStatusView.as_view(), name='update_ride_status'),
    path('rides/<int:ride_id>/track/', TrackDriverLocationView.as_view(), name='track_driver_location'),
    path('rides/rate/', RateRideView.as_view(), name='rate_ride'),
]
