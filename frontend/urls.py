from django.urls import path
from . import views

app_name = 'frontend'  

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('book-ride/', views.book_ride, name='book_ride'),
    path('register-driver/', views.register_driver, name='register_driver'),
    path('logout/', views.logout_view, name='logout'),
]
