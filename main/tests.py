from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .views import get_remaining_time
from django.contrib.auth.models import Group, Permission
from main.models import CustomUser, PasswordChangeRecord, Registration, SiteStatus
from user.models import User, Profile
from django.urls import reverse
from django.core import mail
from django.test import TestCase, Client
from django.contrib.messages import get_messages
from datetime import timedelta
from django.utils import timezone
import time

class GetRemainingTimeTest(TestCase):

    def test_get_remaining_time_valid_case(self):

        created_at = timezone.now() - timedelta(minutes=2)
        expiration_duration_minutes = 3
        remaining_time, minutes, seconds = get_remaining_time(created_at, expiration_duration_minutes)

        self.assertIsNotNone(remaining_time)
        self.assertEqual(minutes, 1)
        self.assertEqual(seconds, 0)

    def test_get_remaining_time_expired_code(self):

        created_at = timezone.now() - timedelta(minutes=5)
        expiration_duration_minutes = 3
        remaining_time, minutes, seconds = get_remaining_time(created_at, expiration_duration_minutes)

        self.assertIsNone(remaining_time)
        self.assertEqual(minutes, 0)
        self.assertEqual(seconds, 0)

    def test_get_remaining_time_exactly_expired(self):

        created_at = timezone.now() - timedelta(minutes=3)
        expiration_duration_minutes = 3
        remaining_time, minutes, seconds = get_remaining_time(created_at, expiration_duration_minutes)

        self.assertIsNone(remaining_time)
        self.assertEqual(minutes, 0)
        self.assertEqual(seconds, 0)

    def test_get_remaining_time_no_creation_time(self):
        created_at = None
        expiration_duration_minutes = 3
        remaining_time, minutes, seconds = get_remaining_time(created_at, expiration_duration_minutes)

        self.assertIsNone(remaining_time)
        self.assertEqual(minutes, 0)
        self.assertEqual(seconds, 0)

    def test_get_remaining_time_invalid_created_at(self):
        created_at = "invalid-date-string"
        expiration_duration_minutes = 3

        with self.assertRaises(ValueError):
            get_remaining_time(created_at, expiration_duration_minutes)


class RegistrationModelTest(TestCase):
    def setUp(self):
        self.registration = Registration.objects.create(
            username="testuser",
            full_name="Test User",
            email="testuser@example.com",
            password="securepassword"
        )

    def test_registration_str(self):
        """Test string representation of Registration model."""
        self.assertEqual(str(self.registration), "testuser")

    def test_registration_fields(self):
        """Test Registration model field values."""
        self.assertEqual(self.registration.username, "testuser")
        self.assertEqual(self.registration.full_name, "Test User")
        self.assertEqual(self.registration.email, "testuser@example.com")
        self.assertTrue(self.registration.registration_date)



class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="securepassword",
            full_name="Test User",
            is_2fa_enabled=True
        )

    def test_custom_user_str(self):
        """Test string representation of CustomUser model."""
        self.assertEqual(str(self.user), "testuser")

    def test_custom_user_fields(self):
        """Test CustomUser model field values."""
        self.assertTrue(self.user.is_2fa_enabled)
        self.assertEqual(self.user.full_name, "Test User")
        self.assertFalse(self.user.is_created_by_createsuperuser)

    def test_custom_user_groups_and_permissions(self):
        """Test adding groups and permissions to CustomUser."""
        group = Group.objects.create(name="Test Group")
        permission = Permission.objects.first()
        self.user.groups.add(group)
        self.user.user_permissions.add(permission)

        self.assertIn(group, self.user.groups.all())
        self.assertIn(permission, self.user.user_permissions.all())

class SiteStatusModelTest(TestCase):
    def setUp(self):
        self.site_status = SiteStatus.objects.create(status=False)

    def test_site_status_str(self):
        """Test string representation of SiteStatus model."""
        self.assertEqual(str(self.site_status), "Block")

    def test_site_status_toggle(self):
        """Test toggling site status."""
        self.site_status.status = True
        self.site_status.save()
        self.assertEqual(str(self.site_status), "Open")

class PasswordChangeRecordModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="SecurePassword123"
        )
        self.record = PasswordChangeRecord.get_or_create_record(self.user)

    def test_password_change_record_str(self):
        """Test string representation of PasswordChangeRecord model."""
        self.assertEqual(str(self.record), "testuser - Password change record")

    def test_update_change_count(self):
        """Test updating change count."""
        initial_count = self.record.change_count
        self.record.update_change_count()
        self.assertEqual(self.record.change_count, initial_count + 1)

    def test_reset_change_count(self):
        """Test resetting change count."""
        self.record.update_change_count()
        self.record.reset_change_count()
        self.assertEqual(self.record.change_count, 0)


class PasswordResetRequestTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('main:password_reset_request')  # URL name cần chính xác
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_valid_email_sends_reset_code(self):
        response = self.client.post(self.url, {'email': 'test@example.com'})
        self.assertRedirects(response, reverse('main:password_reset_code'))
        
        # Kiểm tra nếu mã reset đã được gửi qua email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Your code is:', mail.outbox[0].body)

        # Kiểm tra session chứa các giá trị cần thiết
        self.assertIn('reset_code', self.client.session)
        self.assertIn('user_id', self.client.session)
        self.assertIn('email', self.client.session)
        self.assertIn('code_created_at', self.client.session)

    def test_invalid_email_shows_error_message(self):
        response = self.client.post(self.url, {'email': 'invalid@example.com'})
        self.assertEqual(response.status_code, 200)

        # Kiểm tra thông báo lỗi nếu email không tồn tại
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Email does not exist.')

    def test_get_request_renders_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'password_reset.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['current_step'], 'request')


class HomeViewTestCase(TestCase):
    
    def setUp(self):
        # Tạo người dùng giả
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
    
    def test_home_view_no_query(self):
        # URL của trang home
        url = reverse('main:home')
        response = self.client.get(url)
        
        # Kiểm tra status code
        self.assertEqual(response.status_code, 200)
        
        # Kiểm tra xem form có được render hay không
        self.assertContains(response, 'form')
        
        # Kiểm tra xem các module có được hiển thị trong context không
        self.assertIn('modules', response.context)
        
    def test_home_view_with_query(self):
        url = reverse('main:home') + '?q=test'
        response = self.client.get(url)
        
        # Kiểm tra status code
        self.assertEqual(response.status_code, 200)
        
        # Kiểm tra query được áp dụng trong context
        self.assertIn('modules', response.context)

class LoginViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login_successful(self):
        url = reverse('main:login')
        data = {'username': 'testuser', 'password': 'testpassword'}
        
        response = self.client.post(url, data)
        
        # Kiểm tra xem người dùng có được chuyển hướng sau khi đăng nhập thành công
        self.assertRedirects(response, reverse('main:home'))
    
    def test_login_invalid(self):
        url = reverse('main:login')
        data = {'username': 'testuser', 'password': 'wrongpassword'}
        
        response = self.client.post(url, data)
        
        # Kiểm tra xem có thông báo lỗi không
        self.assertContains(response, "Password is incorrect.")

class Verify2FATestCase(TestCase):
    def setUp(self):
        # Tạo người dùng mới
        self.user = User.objects.create_user(username='testuser', password='password')

        # Đảm bảo người dùng có một đối tượng Profile
        self.profile = Profile.objects.create(user=self.user, two_fa_enabled=True)

        # Đăng nhập người dùng
        self.client.login(username='testuser', password='password')

    def test_2fa_success(self):
        # Giả lập mã xác thực và thời gian tạo
        verification_code = '12'
        session = self.client.session
        session['verification_code'] = verification_code
        session['verification_code_created_at'] = time.time()
        session.save()

        # Gửi yêu cầu với mã xác thực đúng
        url = reverse('main:verify_2fa')
        response = self.client.post(url, {'selected_code': verification_code})

        # Kiểm tra xem người dùng được chuyển hướng đến trang chính sau khi xác thực thành công
        self.assertRedirects(response, reverse('main:home'))

    def test_2fa_code_expiration(self):
        verification_code = '12'
        session = self.client.session
        session['verification_code'] = verification_code
        session['verification_code_created_at'] = time.time() - 3601  # Mã đã hết hạn
        session.save()

        url = reverse('main:verify_2fa')
        response = self.client.post(url, {'selected_code': verification_code})

        # Kiểm tra điều hướng đến trang đăng nhập
        self.assertRedirects(response, reverse('main:login'))

        # Kiểm tra thông báo lỗi tại trang đăng nhập
        response = self.client.get(reverse('main:login'))