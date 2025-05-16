from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import requests
import json
import random
from math import radians, sin, cos, sqrt, atan2

API_BASE_URL = 'http://localhost:8000/api/'

def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách giữa hai điểm tọa độ (km)"""
    R = 6371  # Bán kính Trái Đất (km)
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def find_nearest_driver(pickup_lat, pickup_lng, headers):
    """Tìm tài xế gần nhất đang online"""
    try:
        response = requests.get(f'{API_BASE_URL}drivers/online/', headers=headers)
        if response.status_code == 200:
            drivers = response.json()
            if not drivers:
                return None
            
            # Tính khoảng cách và chọn tài xế gần nhất
            nearest_driver = None
            min_distance = float('inf')
            nearest_drivers = []  # Danh sách tài xế có khoảng cách gần nhất
            
            for driver in drivers:
                if driver.get('last_latitude') and driver.get('last_longitude'):
                    distance = haversine_distance(
                        pickup_lat,
                        pickup_lng,
                        float(driver['last_latitude']),
                        float(driver['last_longitude'])
                    )
                    if distance < min_distance:
                        min_distance = distance
                        nearest_drivers = [driver]
                    elif distance == min_distance:
                        nearest_drivers.append(driver)
            
            # Chọn ngẫu nhiên nếu có nhiều tài xế ở cùng khoảng cách
            if nearest_drivers:
                nearest_driver = random.choice(nearest_drivers)
            
            return nearest_driver
    except requests.RequestException:
        return None

def home(request):
    role = request.session.get('role', '')
    access_token = request.session.get('access_token', '')
    trip_history = []
    
    if access_token:
        headers = {'Authorization': f'Token {access_token}'}
        try:
            response = requests.get(f'{API_BASE_URL}rides/history/', headers=headers)
            if response.status_code == 200:
                trip_history = response.json()
        except requests.RequestException:
            messages.error(request, 'Không thể lấy lịch sử chuyến đi.')
    
    return render(request, 'home.html', {'role': role, 'trip_history': trip_history})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            response = requests.post(f'{API_BASE_URL}auth/login/', data={
                'email': email,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                request.session['access_token'] = data['access_token']
                request.session['username'] = data['username']
                request.session['role'] = data['role']
                messages.success(request, 'Đăng nhập thành công!')
                return redirect('frontend:home')
            else:
                messages.error(request, 'Email hoặc mật khẩu không đúng.')
        except requests.RequestException:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'login.html')

def logout_view(request):
    if request.method == 'POST':
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
    
    headers = {'Authorization': f'Token {access_token}'}
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
    except requests.RequestException:
        messages.error(request, 'Không thể lấy thông tin hồ sơ.')
    
    return render(request, 'profile.html', {'profile': profile_data})

def register_driver(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để đăng ký làm tài xế.')
        return redirect('frontend:login')
    
    headers = {'Authorization': f'Token {access_token}'}
    is_driver = False
    profile = {}
    
    try:
        response = requests.get(f'{API_BASE_URL}profile/', headers=headers)
        if response.status_code == 200:
            profile = response.json()
            is_driver = profile.get('is_driver', False)
    except requests.RequestException:
        messages.error(request, 'Không thể lấy thông tin hồ sơ.')
    
    if request.method == 'POST' and not is_driver:
        form_data = {
            'username': request.POST.get('username'),
            'phone': request.POST.get('phone'),
            'email': request.POST.get('email'),
            'id_number': request.POST.get('id_number'),
            'license_number': request.POST.get('license_number'),
            'license_plate': request.POST.get('license_plate'),
            'brand': request.POST.get('brand'),
            'model': request.POST.get('model'),
            'year': request.POST.get('year')
        }
        
        try:
            response = requests.post(f'{API_BASE_URL}drivers/register/', headers=headers, data=form_data, files={
                'driver_license': request.FILES.get('driver_license'),
                'vehicle_photo': request.FILES.get('vehicle_photo')
            })
            
            if response.status_code == 201:
                messages.success(request, 'Đăng ký tài xế thành công! Đang chờ phê duyệt.')
                return redirect('frontend:register_driver')
            else:
                messages.error(request, response.json().get('error', 'Có lỗi xảy ra.'))
        except requests.RequestException:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'register_driver.html', {'is_driver': is_driver, 'profile': profile})

def ride_tracking(request, ride_id):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để theo dõi chuyến đi.')
        return redirect('frontend:login')
    
    headers = {'Authorization': f'Token {access_token}'}
    ride_data = {}
    
    try:
        response = requests.get(f'{API_BASE_URL}rides/{ride_id}/', headers=headers)
        if response.status_code == 200:
            ride_data = response.json()
        else:
            messages.error(request, 'Không thể lấy thông tin chuyến đi.')
    except requests.RequestException:
        messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'ride_tracking.html', {'ride': ride_data})

def book_ride(request):
    if request.method == 'POST':
        access_token = request.session.get('access_token')
        if not access_token:
            messages.error(request, 'Vui lòng đăng nhập để đặt chuyến đi.')
            return redirect('frontend:login')
        
        headers = {'Authorization': f'Token {access_token}'}
        try:
            # Tạo chuyến đi
            response = requests.post(f'{API_BASE_URL}rides/book/', headers=headers, data={
                'pickup_location': request.POST.get('pickup_location'),
                'destination_location': request.POST.get('destination_location'),
                'pickup_lat': request.POST.get('pickup_lat'),
                'pickup_lng': request.POST.get('pickup_lng'),
                'dest_lat': request.POST.get('dest_lat'),
                'dest_lng': request.POST.get('dest_lng'),
                'vehicle_type': request.POST.get('vehicle_type')
            })
            
            if response.status_code == 201:
                ride_data = response.json()
                ride_id = ride_data.get('id')
                
                # Tự động gán tài xế
                nearest_driver = find_nearest_driver(
                    float(request.POST.get('pickup_lat', 0)),
                    float(request.POST.get('pickup_lng', 0)),
                    headers
                )
                
                if nearest_driver:
                    assign_response = requests.post(
                        f'{API_BASE_URL}rides/{ride_id}/assign/',
                        headers=headers,
                        json={'driver_id': nearest_driver['id']}
                    )
                    if assign_response.status_code == 200:
                        messages.success(request, 'Đặt chuyến đi thành công! Tài xế đã được gán.')
                        return JsonResponse({'success': True, 'ride_id': ride_id})
                    else:
                        messages.error(request, 'Không thể gán tài xế. Vui lòng thử lại.')
                        return JsonResponse({'success': False, 'error': 'Không thể gán tài xế'})
                else:
                    messages.error(request, 'Không tìm thấy tài xế phù hợp.')
                    return JsonResponse({'success': False, 'error': 'Không tìm thấy tài xế'})
            else:
                messages.error(request, response.json().get('error', 'Có lỗi xảy ra.'))
                return JsonResponse({'success': False, 'error': response.json().get('error', 'Có lỗi xảy ra')})
        except requests.RequestException:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
            return JsonResponse({'success': False, 'error': 'Có lỗi xảy ra'})
    
    return render(request, 'book_ride.html')

def history(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để xem lịch sử chuyến đi.')
        return redirect('frontend:login')
    
    headers = {'Authorization': f'Token {access_token}'}
    trip_history = []
    
    try:
        response = requests.get(f'{API_BASE_URL}rides/history/', headers=headers)
        if response.status_code == 200:
            trip_history = response.json()
        else:
            messages.error(request, 'Không thể lấy lịch sử chuyến đi.')
    except requests.RequestException:
        messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'history.html', {'trip_history': trip_history})

def about(request):
    return render(request, 'about.html')

def driver_dashboard(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để xem bảng điều khiển tài xế.')
        return redirect('frontend:login')
    
    headers = {'Authorization': f'Token {access_token}'}
    profile = {}
    active_ride = None
    
    try:
        response = requests.get(f'{API_BASE_URL}profile/', headers=headers)
        if response.status_code == 200:
            profile = response.json()
        else:
            messages.error(request, 'Không thể lấy thông tin hồ sơ.')
        
        response = requests.get(f'{API_BASE_URL}rides/active/', headers=headers)
        if response.status_code == 200:
            active_ride = response.json().get('ride')
    except requests.RequestException:
        messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'driver_dashboard.html', {
        'profile': profile,
        'active_ride': active_ride
    })

def driver_ride(request, ride_id):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để quản lý chuyến đi.')
        return redirect('frontend:login')
    
    headers = {'Authorization': f'Token {access_token}'}
    ride_data = {}
    
    try:
        response = requests.get(f'{API_BASE_URL}rides/{ride_id}/', headers=headers)
        if response.status_code == 200:
            ride_data = response.json()
        else:
            messages.error(request, 'Không thể lấy thông tin chuyến đi.')
    except requests.RequestException:
        messages.error(request, 'Có lỗi xảy ra. Vui lòng thử lại sau.')
    
    return render(request, 'driver_ride.html', {'ride': ride_data})
