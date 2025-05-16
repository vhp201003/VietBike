from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('register_driver/', views.register_driver, name='register_driver'),
    path('ride/<int:ride_id>/', views.ride_tracking, name='ride_tracking'),
    path('book_ride/', views.book_ride, name='book_ride'),
    path('history/', views.history, name='history'),
    path('about/', views.about, name='about'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('ride/driver/<int:ride_id>/', views.driver_ride, name='driver_ride'),
]
