from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from backend.models import DriverProfile
import requests
import os

API_BASE_URL = settings.BACKEND_API_URL + '/'

def home(request):
    role = request.session.get('role', '')
    return render(request, 'home.html', {'role': role})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            response = requests.post(f'{API_BASE_URL}token/', data={
                'email': email,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                request.session['access_token'] = data['access']
                request.session['refresh_token'] = data['refresh']
                headers = {'Authorization': f'Bearer {data["access"]}'}
                user_response = requests.get(f'{API_BASE_URL}profile/', headers=headers)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    request.session['username'] = user_data.get('username', '')
                    request.session['role'] = user_data.get('role', '')
                messages.success(request, 'Đăng nhập thành công!')
                return redirect('frontend:home')
            else:
                messages.error(request, 'Email hoặc mật khẩu không đúng.')
        except requests.RequestException:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'login.html')

def logout_view(request):
    if request.method == 'POST':
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')
        if access_token and refresh_token:
            try:
                headers = {'Authorization': f'Bearer {access_token}'}
                response = requests.post(f'{API_BASE_URL}users/logout/', headers=headers, data={'refresh': refresh_token})
                if response.status_code != 200:
                    messages.error(request, 'Có lỗi khi đăng xuất.')
            except requests.RequestException:
                messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
        
        request.session.flush()
        messages.success(request, 'Đăng xuất thành công!')
        return redirect('frontend:login')
    return redirect('frontend:home')

def register(request):
    if request.method == 'POST':
        try:
            response = requests.post(f'{API_BASE_URL}auth/register/', data={
                'username': request.POST.get('username'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone'),
                'password': request.POST.get('password')
            })
            
            if response.status_code == 201:
                messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
                return redirect('frontend:login')
            else:
                messages.error(request, response.json().get('error', 'Có lỗi xảy ra.'))
        except requests.RequestException:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'register.html')

def profile(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để xem hồ sơ.')
        return redirect('frontend:login')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_data = {}
    
    if request.method == 'POST':
        form_data = {
            'username': request.POST.get('username'),
            'phone': request.POST.get('phone'),
            'email': request.POST.get('email'),
            'old_password': request.POST.get('old_password'),
            'new_password': request.POST.get('new_password'),
            'remove_image': request.POST.get('remove_image')
        }
        
        try:
            response = requests.put(f'{API_BASE_URL}profile/update/', headers=headers, data=form_data, files={
                'profile_picture': request.FILES.get('profile_picture')
            })
            
            if response.status_code == 200:
                messages.success(request, 'Cập nhật hồ sơ thành công!')
                profile_data = response.json()
            else:
                messages.error(request, response.json().get('error', 'Có lỗi xảy ra.'))
        except requests.RequestException:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    try:
        response = requests.get(f'{API_BASE_URL}profile/', headers=headers)
        if response.status_code == 200:
            profile_data = response.json()
        else:
            messages.error(request, 'Không thể lấy thông tin hồ sơ.')
    except requests.RequestException:
        messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'profile.html', {'profile': profile_data})

def about(request):
    return render(request, 'about.html')

def history(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để xem lịch sử chuyến đi.')
        return redirect('frontend:login')

    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        response = requests.get(f'{API_BASE_URL}rides/history/', headers=headers)
        if response.status_code == 200:
            rides = response.json().get('rides', [])
        else:
            rides = []
            messages.error(request, 'Không thể lấy lịch sử chuyến đi.')
    except requests.RequestException:
        rides = []
        messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')

    return render(request, 'history.html', {'rides': rides})

def book_ride(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để đặt chuyến đi.')
        return redirect('frontend:login')

    if request.method == 'POST':
        pickup_location = request.POST.get('pickup_location')
        destination_location = request.POST.get('destination_location')

        if not pickup_location or not destination_location:
            messages.error(request, 'Vui lòng nhập đầy đủ điểm đón và điểm đến.')
            return redirect('frontend:home')

        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.post(f'{API_BASE_URL}rides/request/', headers=headers, json={
                'start_location': pickup_location,
                'end_location': destination_location
            })
            if response.status_code == 201:
                messages.success(request, 'Yêu cầu chuyến đi thành công! Đang tìm tài xế...')
            else:
                messages.error(request, response.json().get('error', 'Có lỗi xảy ra khi đặt chuyến đi.'))
        except requests.RequestException:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
        return redirect('frontend:home')

    return redirect('frontend:home')

@login_required
def register_driver(request):
    if request.user.role != 'driver':
        messages.error(request, 'Chỉ tài xế mới có thể truy cập trang này.')
        return redirect('frontend:home')

    try:
        driver_profile = request.user.driverprofile
        is_driver = True
    except DriverProfile.DoesNotExist:
        driver_profile = None
        is_driver = False

    profile_data = {
        'username': request.user.username,
        'phone': request.user.phone if hasattr(request.user, 'phone') else '',
        'email': request.user.email,
        'is_available': driver_profile.is_available if driver_profile else False,
        'profile_picture': driver_profile.profile_picture if driver_profile else None,
    }

    if request.method == 'POST':
        if is_driver:
            # Xử lý trạng thái online/offline
            is_available = request.POST.get('is_available') == 'true'
            driver_profile.is_available = is_available
            driver_profile.save()
            messages.success(request, f'Đã {"bật" if is_available else "tắt"} kết nối.')
            return redirect('frontend:register_driver')
        else:
            # Xử lý form đăng ký tài xế
            username = request.POST.get('username')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            id_number = request.POST.get('id_number')
            license_number = request.POST.get('license_number')
            license_plate = request.POST.get('license_plate')
            brand = request.POST.get('brand')
            model = request.POST.get('model')
            year = request.POST.get('year')
            driver_license = request.FILES.get('driver_license')
            vehicle_photo = request.FILES.get('vehicle_photo')

            # Kiểm tra các trường bắt buộc
            required_fields = [username, phone, email, id_number, license_number, license_plate, brand, model, year, driver_license, vehicle_photo]
            if not all(required_fields):
                messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
                return render(request, 'register_driver.html', {
                    'is_driver': is_driver,
                    'profile': profile_data,
                })

            # Kiểm tra kích thước file
            max_size = 5 * 1024 * 1024  # 5MB
            if driver_license.size > max_size or vehicle_photo.size > max_size:
                messages.error(request, 'File ảnh không được vượt quá 5MB.')
                return render(request, 'register_driver.html', {
                    'is_driver': is_driver,
                    'profile': profile_data,
                })

            # Cập nhật thông tin người dùng
            request.user.username = username
            request.user.email = email
            if hasattr(request.user, 'phone'):
                request.user.phone = phone
            request.user.save()

            # Tạo DriverProfile
            driver_profile = DriverProfile.objects.create(
                user=request.user,
                id_number=id_number,
                license_number=license_number,
                license_plate=license_plate,
                brand=brand,
                model=model,
                year=year,
                driver_license=driver_license,
                vehicle_photo=vehicle_photo,
                is_available=True,
            )
            messages.success(request, 'Đăng ký tài xế thành công!')
            return redirect('frontend:register_driver')

    return render(request, 'register_driver.html', {
        'is_driver': is_driver,
        'profile': profile_data,
    })

def driver_dashboard(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để xem bảng điều khiển tài xế.')
        return redirect('frontend:login')
    
    headers = {'Authorization': f'Token {access_token}'}
    profile = {}
    active_ride = None
    
    # Kiểm tra xem người dùng có phải tài xế không
    try:
        driver_profile = request.user.driverprofile_set.first()
        if not driver_profile:
            messages.error(request, 'Bạn chưa đăng ký làm tài xế. Vui lòng đăng ký trước.')
            return redirect('frontend:register_driver')
    except Exception:
        messages.error(request, 'Có lỗi khi kiểm tra thông tin tài xế.')
        return redirect('frontend:home')
    
    # Gọi API để lấy thông tin
    try:
        response = requests.get(f'{API_BASE_URL}profile/', headers=headers)
        if response.status_code == 200:
            profile = response.json()
        else:
            messages.error(request, f'Không thể lấy thông tin hồ sơ. Mã lỗi: {response.status_code}')
        
        response = requests.get(f'{API_BASE_URL}rides/active/', headers=headers)
        if response.status_code == 200:
            active_ride = response.json().get('ride')
        else:
            messages.warning(request, f'Không tìm thấy chuyến đi đang hoạt động. Mã lỗi: {response.status_code}')
    except requests.RequestException as e:
        messages.error(request, f'Có lỗi kết nối với máy chủ: {str(e)}')
    
    return render(request, 'driver_dashboard.html', {
        'profile': profile,
        'active_ride': active_ride
    })
