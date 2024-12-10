from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, CustomLoginForm, EmailForm, ConfirmationCodeForm
from django.contrib.auth import authenticate, login
from user.models import User, Profile, Role
from module_group.forms import ExcelImportForm
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .forms import PasswordResetRequestForm, PasswordResetCodeForm, PasswordResetForm
from django.utils import timezone
from datetime import timedelta, datetime
import random
from django.conf import settings
from .module_utils import get_grouped_modules
from .models import SiteStatus
from django.contrib.auth.decorators import user_passes_test
from activity.models import UserActivityLog
import string
from django.http import JsonResponse

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                random_code = get_random_string(length=6)

                request.session['reset_code'] = random_code
                request.session['user_id'] = user.id
                request.session['email'] = email
                request.session['code_created_at'] = timezone.now().isoformat()

                send_mail(
                    'Password Reset Code',
                    f'Your code is: {random_code}',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
                return redirect('main:password_reset_code')
            except User.DoesNotExist:
                messages.error(request, 'Email does not exist.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'password_reset.html', {'form': form, 'current_step': 'request'})


def get_remaining_time(created_at, expiration_duration_minutes):
    if created_at:
        if isinstance(created_at, str):
            created_at = timezone.datetime.fromisoformat(created_at)

        if created_at.tzinfo is None:
            created_at = timezone.make_aware(created_at, timezone.get_current_timezone())

        expiration_time = created_at + timedelta(minutes=expiration_duration_minutes)

        current_time = timezone.now()

        if expiration_time.tzinfo is None:
            expiration_time = timezone.make_aware(expiration_time, timezone.get_current_timezone())

        if current_time.tzinfo is None:
            current_time = timezone.make_aware(current_time, timezone.get_current_timezone())

        remaining_time = expiration_time - current_time

        if remaining_time.total_seconds() >= 0:
            minutes = remaining_time.seconds // 60
            seconds = remaining_time.seconds % 60
            return remaining_time, minutes, seconds

    return None, 0, 0

def password_reset_code(request):
    created_at = request.session.get('code_created_at')
    expiration_duration_minutes = 3
    remaining_time, minutes, seconds = get_remaining_time(created_at, expiration_duration_minutes)

    if remaining_time is None:
        minutes = 0
        seconds = 0

    if request.method == 'POST':
        form = PasswordResetCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            session_code = request.session.get('reset_code')

            if session_code and created_at:
                if code == session_code and remaining_time and remaining_time.total_seconds() > 0:
                    messages.success(request, 'The verification code is valid. Please enter a new password.')
                    return redirect('main:password_reset_form')
                else:
                    messages.error(request, 'The code has expired or is invalid.')
            else:
                messages.error(request, 'The code is invalid.')
        else:
            messages.error(request, 'An error occurred. Please check your code.')
    else:
        form = PasswordResetCodeForm()

    return render(request, 'password_reset.html', {
        'form': form,
        'current_step': 'code',
        'remaining_time': remaining_time,
        'minutes': minutes,
        'seconds': seconds
    })



def resend_code_auto(request):
    email = request.session.get('email')

    if email:
        user = User.objects.filter(email=email).first()
        
        if user:
            random_code = get_random_string(length=6)

            request.session['reset_code'] = random_code
            request.session['code_created_at'] = timezone.now().isoformat()

            try:
                send_mail(
                    'Password Reset Verification Code',
                    f'Your verification code is: {random_code}',
                    'no-reply@yourdomain.com',
                    [email],
                    fail_silently=False,
                )

                messages.success(request, 'The verification code has been resent to your email.')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
        else:
            messages.error(request, 'User with this email does not exist.')
    else:
        messages.error(request, 'Email not found. Please try again.')

    return redirect('main:password_reset_code')


def password_reset_form(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user_id = request.session.get('user_id')
            if user_id:
                user = User.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully.')
                del request.session['reset_code']
                del request.session['user_id']
                return redirect('main:home')
    else:
        form = PasswordResetForm()
    
    return render(request, 'password_reset.html', {'form': form, 'current_step': 'reset'})


def register_email(request):
    if request.method == 'POST':
        email_form = EmailForm(request.POST)
        if email_form.is_valid():
            email = email_form.cleaned_data['email']
            confirmation_code = random.randint(1000, 9999)  # Tạo mã xác thực
            request.session['confirmation_code'] = confirmation_code
            request.session['email'] = email
            
            # Gửi mã xác thực qua email
            send_mail(
                'Account Registration Successful',
                f'Hello,\n\n'
                f'You have successfully registered an account on the system.\n\n'
                f'Your confirmation code is: {confirmation_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return redirect('main:register_confirmation_code')
    else:
        email_form = EmailForm()
    
    return render(request, 'register_email.html', {'form': email_form})


def user_exists(email):
    return User.objects.filter(email=email).exists()


def register_confirmation_code(request):
    if request.method == 'POST':
        confirmation_code_form = ConfirmationCodeForm(request.POST)
        if confirmation_code_form.is_valid():
            code = confirmation_code_form.cleaned_data['confirmation_code']
            if code == str(request.session.get('confirmation_code')):
                # Lấy email từ session
                email = request.session.get('email')

                # Kiểm tra xem người dùng đã tồn tại chưa
                if user_exists(email):
                    messages.error(request, "This email is already in use. Please log in or use a different email!")
                    return redirect('main:register_email')

                # Lưu email vào session để sử dụng sau
                request.session['email_verified'] = email

                messages.success(request, "Email verification successful! Please fill in your registration details.")
                return redirect('main:register_user_info')  # Chuyển hướng đến thông tin người dùng
            else:
                messages.error(request, "Invalid confirmation code.")
    else:
        confirmation_code_form = ConfirmationCodeForm()
    
    return render(request, 'register_confirmation_code.html', {'form': confirmation_code_form})


def register_user_info(request):
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        if user_form.is_valid():
            email = request.session.get('email_verified')
            
            # Kiểm tra xem người dùng đã tồn tại chưa
            if user_exists(email):
                messages.error(request, "A user already exists with this email!")
                return redirect('main:register_email')

            user = user_form.save(commit=False)  # Không lưu ngay
            user.email = email  # Lưu email vào user
            user.set_password(user_form.cleaned_data.get('password1'))  # Lưu mật khẩu đã mã hóa
            user.save()  # Lưu user
            
            # Tạo Profile cho user
            profile = Profile.objects.create(user=user)  # Chỉ tạo Profile
            
            # Gán vai trò mặc định là User
            default_role = Role.objects.get(role_name='Student')  
            profile.role = default_role
            profile.email_verified = True  # Đánh dấu email là đã xác thực
            profile.save()  # Lưu Profile với vai trò mặc định

            # Lưu user_id vào session
            request.session['user_id'] = user.id  # Lưu ID người dùng vào session
            
            messages.success(request, "Registration successful!")
            return redirect('main:login')
    else:
        user_form = RegistrationForm()
    
    return render(request, 'register_user_info.html', {'form': user_form})


def check_username(request):
    username = request.GET.get('username', None)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'exists': True})
    return JsonResponse({'exists': False})

from course.models import Course
def home(request):
    query = request.GET.get('q')
    temporary_role_id = request.session.get('temporary_role')
    courses = Course.objects.all()

    module_groups, grouped_modules = get_grouped_modules(request.user, temporary_role_id)

    # Lọc modules dựa trên truy vấn tìm kiếm
    if query:
        modules = [module for modules in grouped_modules.values() for module in modules]
        modules = [module for module in modules if query.lower() in module.module_name.lower() or query.lower() in module.module_group.group_name.lower()]
    else:
        modules = [module for modules in grouped_modules.values() for module in modules]

    form = ExcelImportForm()

    return render(request, 'home.html', {
        'module_groups': module_groups,
        'modules': modules,
        'grouped_modules': grouped_modules,
        'form': form,
        'courses': courses,
    })



def login_view(request):
    current_week = timezone.now().isocalendar()[1]  # Lấy tuần hiện tại trong năm
    user_sessions = request.session.get('user_login_stats', {})

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Đăng nhập thành công
                if str(current_week) not in user_sessions:
                    user_sessions[str(current_week)] = {'successful_logins': 0, 'failed_logins': 0}

                user_sessions[str(current_week)]['successful_logins'] += 1
                request.session['user_login_stats'] = user_sessions  # Lưu lại vào session

                # Thêm bản ghi vào UserActivityLog khi đăng nhập thành công
                UserActivityLog.objects.create(
                    user=user,
                    activity_type='login',
                    activity_details='success',
                    activity_timestamp=timezone.now()
                )

                request.session['username'] = username
                request.session['password'] = password

                # Kiểm tra tài khoản có bị khóa hay không không cần thiết nữa vì đã kiểm tra trong form
                if user.is_superuser:
                    login(request, user)
                    messages.success(request, "Login Sucessfully")
                    return redirect('main:home')

                # Check for user profile and 2FA
                try:
                    profile = Profile.objects.get(user=user)
                    is_2fa_enabled = profile.two_fa_enabled
                except Profile.DoesNotExist:
                    is_2fa_enabled = False
                
                user_role = user.profile.role.role_name if hasattr(user, 'profile') and hasattr(user.profile, 'role') else None

                # Handle 2FA if enabled
                if is_2fa_enabled:
                    verification_code = get_random_string(length=2, allowed_chars='0123456789')
                    request.session['verification_code'] = verification_code
                    request.session['verification_code_created_at'] = timezone.now().timestamp()
                    send_mail(
                        '2FA Verification',
                        f'Your verification code is: {verification_code}',
                        'your-email@example.com',
                        [user.email],
                        fail_silently=False,
                    )
                    return redirect('main:verify_2fa')

                # Redirect based on user role
                else:
                    login(request, user)  # Log in the user
                    if user_role == 'Student':
                        return redirect('student_portal:course_list')
                    else:
                        next_url = request.GET.get('next', 'main:home')
                        return redirect(next_url)
            else:
                messages.error(request, "Incorrect login information.")
        else:
            for field in form.errors:
                for error in form.errors[field]:
                    messages.error(request, error)
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})


def verify_2fa(request):
    # Check if the user is not authenticated
    if not request.user.is_authenticated:
        username = request.session.get('username')
        password = request.session.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            else:
                messages.error(request, "Your login session has expired. Please log in again.")
                return redirect('main:login')
        else:
            messages.error(request, "Your login session has expired. Please log in again.")
            return redirect('main:login')

    try:
        profile = Profile.objects.get(user=request.user)
        is_2fa_enabled = profile.two_fa_enabled
    except Profile.DoesNotExist:
        is_2fa_enabled = False

    if not is_2fa_enabled:
        messages.success(request, "2FA verification is disabled. Login successful.")
        return redirect('main:home')

    if request.method == 'POST':
        selected_code = request.POST.get('selected_code')
        session_code = request.session.get('verification_code')
        code_created_at = request.session.get('verification_code_created_at')
        failed_attempts = request.session.get('failed_2fa_attempts', 0)

        current_time = timezone.now().timestamp()
        if code_created_at is None or (current_time - code_created_at) > 20:
            messages.error(request, "The verification code has expired. Please log in again.")
            return redirect('main:login')

        if selected_code == session_code:
            # Remove session data after successful verification
            for key in ['username', 'password', 'verification_code', 'verification_code_created_at', 'failed_2fa_attempts', 'resend_count']:
                request.session.pop(key, None)
            messages.success(request, "Login successful with 2FA!")
            return redirect('main:home')

        else:
            # Increment the failed attempts and save the count
            failed_attempts += 1
            request.session['failed_2fa_attempts'] = failed_attempts

            # If the user enters the wrong code, send a new verification code
            if failed_attempts < 3:
                verification_code = str(random.randint(10, 99))
                request.session['verification_code'] = verification_code
                request.session['verification_code_created_at'] = timezone.now().timestamp()
                request.session['resend_count'] = request.session.get('resend_count', 0) + 1

                user_email = request.user.email
                send_mail(
                    'New Verification Code',
                    f'Your verification code is: {verification_code}. Please try again.',
                    'your-email@example.com',
                    [user_email],
                    fail_silently=False,
                )
                messages.error(request, "The verification code is incorrect. A new code has been sent to your email.")
                return redirect('main:verify_2fa')

            # If the user exceeds 3 failed attempts, send a warning email
            if failed_attempts >= 3:
                user_email = request.user.email
                send_mail(
                    'Warning: Multiple Failed 2FA Attempts',
                    'You have entered the incorrect verification code more than 3 times. Please check your account.',
                    'your-email@example.com',
                    [user_email],
                    fail_silently=False,
                )

                # Log the activity
                UserActivityLog.objects.create(
                    user=request.user,
                    activity_type='2fa_email_notification',
                    activity_details='Email sent after multiple failed 2FA attempts',
                    activity_timestamp=timezone.now()
                )

                # Reset the failed attempts counter
                request.session['failed_2fa_attempts'] = 0
                messages.error(request, "You have entered the incorrect verification code too many times. An email has been sent to notify you.")
                return redirect('main:login')

            messages.error(request, "The verification code is incorrect. Please try again.")
            return redirect('main:verify_2fa')


    # Send verification code if it's not in the session
    if is_2fa_enabled and 'verification_code' not in request.session:
        verification_code = str(random.randint(10, 99))
        request.session['verification_code'] = verification_code
        request.session['verification_code_created_at'] = timezone.now().timestamp()
        request.session['resend_count'] = 1  # Start counting from 1

        user_email = request.user.email
        send_mail(
            'Your 2FA Verification Code',
            f'Your verification code is: {verification_code}',
            'your-email@example.com',
            [user_email],
            fail_silently=False,
        )

    verification_code = request.session.get('verification_code')
    other_choices = random.sample([str(i) for i in range(10, 100) if str(i) != verification_code], 5)
    choices = [verification_code] + other_choices
    random.shuffle(choices)

    return render(request, 'verify_2fa.html', {'choices': choices})


def toggle_2fa(request, pk):
    # Get the profile for the logged-in user
    profile = Profile.objects.get(user=request.user)
    user = get_object_or_404(User, pk=pk)
    
    # Check if the user is a superuser
    if user.is_superuser:
        messages.warning(request, "Superuser accounts cannot enable/disable 2FA.")
        return redirect('user:user_detail', pk=user.pk)

    # If 2FA is enabled and the user wants to disable it
    if profile.two_fa_enabled:
        # Generate a random confirmation token and store it in the session
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        expiration_time = timezone.now() + timedelta(minutes=10)  # Token valid for 10 minutes

        # Store the confirmation token in the session
        request.session['two_fa_token'] = token
        request.session['two_fa_expiration'] = expiration_time.isoformat()

        # Create the confirmation link for the user
        confirm_link = request.build_absolute_uri(f"/confirm_2fa/{token}/")

        # Send confirmation email
        send_mail(
            'Confirm Disable 2FA (Two-Factor Authentication)',
            f'Do you want to disable 2FA?\n\n'
            f'Please click the link below to confirm:\n\n'
            f'Confirm: {confirm_link}',
            'admin@yourdomain.com',
            [user.email],
            fail_silently=False,
        )

        messages.info(request, "A confirmation email has been sent. Please check your email to disable 2FA.")
        return redirect('user:user_detail', pk=user.pk)

    # If 2FA is not enabled, toggle the setting
    profile.two_fa_enabled = not profile.two_fa_enabled
    profile.save()

    messages.success(request, "The 2FA status has been changed.")
    return redirect('user:user_detail', pk=user.pk)


def confirm_2fa(request, token):
    # Check the confirmation token in the session
    session_token = request.session.get('two_fa_token')
    session_expiration = request.session.get('two_fa_expiration')

    if session_token != token or not session_expiration:
        messages.error(request, "Invalid confirmation token.")
        return redirect('user:user_list')  # Or redirect to another page if needed

    # Use datetime.fromisoformat instead of timezone.fromisoformat
    expiration_time = datetime.fromisoformat(session_expiration)

    if timezone.now() > expiration_time:
        messages.error(request, "The confirmation token has expired.")
        return redirect('user:user_list')  # Or redirect to another page if needed

    # Get the user's profile
    profile = Profile.objects.get(user=request.user)

    # Check if 2FA was already disabled, do nothing if so
    if not profile.two_fa_enabled:
        messages.info(request, "2FA has already been disabled.")
        return redirect('user:user_detail', pk=request.user.pk)

    # Disable 2FA
    profile.two_fa_enabled = False
    profile.save()

    # Immediately remove the confirmation token from the session
    del request.session['two_fa_token']
    del request.session['two_fa_expiration']

    messages.success(request, "2FA has been disabled.")

    # Redirect back to the user's detail page
    return redirect('user:user_detail', pk=request.user.pk)


@user_passes_test(lambda u: u.is_superuser)
def lock_site(request):
    # Lấy bản ghi SiteStatus hoặc tạo mới nếu không có
    site_status, created = SiteStatus.objects.get_or_create(id=1)

    # Đặt trạng thái thành True (Khóa)
    site_status.status =  False
    site_status.save()

    # Quay lại trang admin sau khi cập nhật
    return redirect('admin:index')

@user_passes_test(lambda u: u.is_superuser)
def unlock_site(request):
    # Lấy bản ghi SiteStatus hoặc tạo mới nếu không có
    site_status, created = SiteStatus.objects.get_or_create(id=1)

    # Đặt trạng thái thành False (Mở)
    site_status.status = True
    site_status.save()

    # Quay lại trang admin sau khi cập nhật
    return redirect('admin:index')