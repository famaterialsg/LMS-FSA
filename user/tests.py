from django.test import TestCase, Client
from django.urls import reverse
from user.models import User, Profile, Student, Permission
from role.models import Role
from django.contrib.messages import get_messages
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

class UserAddViewTest(TestCase):

    def setUp(self):
        # Tạo role
        self.role_student = Role.objects.create(role_name='Student')
        self.role_manager = Role.objects.create(role_name='Manager')

        # Tạo superuser
        self.superuser = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='123456'
        )

        # Tạo người dùng thường với profile
        self.user_with_profile = User.objects.create_user(
            username='testuser', email='testuser@example.com', password='test123'
        )
        self.profile = Profile.objects.create(user=self.user_with_profile, role=self.role_student)

        # URL cho view
        self.url = reverse('user:user_add')

        # Client để gửi request
        self.client = Client()

    def test_user_add_no_permission(self):
        # Đăng nhập với người dùng không có quyền
        self.client.login(username='testuser', password='test123')
        response = self.client.get(self.url)

        # Kiểm tra phản hồi và thông báo lỗi
        self.assertRedirects(response, reverse('user:user_list'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Bạn không có quyền.")

    def test_user_add_superuser_access(self):
        # Đăng nhập với superuser
        self.client.login(username='admin', password='123456')
        response = self.client.get(self.url)

        # Kiểm tra hiển thị form
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_form.html')

    def test_user_add_valid_data(self):
        # Đăng nhập với superuser
        self.client.login(username='admin', password='123456')

        # Dữ liệu hợp lệ để thêm người dùng
        data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'role': self.role_student.id,
            'password1': 'StrongP@ssw0rd',
            'password2': 'StrongP@ssw0rd',
            'profile_picture_url': 'http://example.com/pic.jpg',
            'bio': 'New user bio',
            'interests': 'Coding, Reading',
            'learning_style': 'Visual',
            'preferred_language': 'English',
            'student_code': 'S12345'
        }

        response = self.client.post(self.url, data)

        # Kiểm tra người dùng được tạo
        self.assertRedirects(response, reverse('user:user_list'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertEqual(user.profile.bio, 'New user bio')
        self.assertTrue(Student.objects.filter(user=user, student_code='S12345').exists())

    def test_user_add_invalid_data(self):
        # Đăng nhập với superuser
        self.client.login(username='admin', password='123456')

        # Dữ liệu không hợp lệ (password không khớp)
        data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'role': self.role_student.id,
            'password1': 'StrongP@ssw0rd',
            'password2': 'WeakPass',
        }

        response = self.client.post(self.url, data)

        # Kiểm tra form báo lỗi
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertFalse(User.objects.filter(username='newuser').exists())



class UserExportTestCase(TestCase):
    def setUp(self):
        # Tạo các vai trò và quyền thử nghiệm
        self.admin_role = Role.objects.create(role_name='Admin')
        self.user_role = Role.objects.create(role_name='User')

        # Tạo người dùng admin (siêu người dùng)
        self.admin_user = User.objects.create_user(username='admin', password='password')
        self.admin_user.is_superuser = True  # Đảm bảo người dùng này là siêu người dùng
        self.admin_user.save()

        # Tạo Profile cho admin
        self.admin_profile = Profile.objects.create(user=self.admin_user, role=self.admin_role)

        # Tạo người dùng thường
        self.regular_user = User.objects.create_user(username='user', password='password')

        # Tạo Profile cho người dùng thường
        self.regular_profile = Profile.objects.create(user=self.regular_user, role=self.user_role)

    def test_export_users_permission(self):
        # Đăng nhập người dùng admin
        self.client.login(username='admin', password='password')

        # Kiểm tra với định dạng hợp lệ (xlsx)
        response = self.client.get(reverse('user:export_users') + '?format=xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_export_users_no_permission(self):
        # Đăng nhập người dùng thường
        self.client.login(username='user', password='password')

        # Người dùng thường không có quyền xuất dữ liệu
        response = self.client.get(reverse('user:export_users') + '?format=xlsx')
        self.assertEqual(response.status_code, 302)  # Phải chuyển hướng
        self.assertRedirects(response, reverse('user:user_list'))

    def test_export_users_with_role(self):
        # Đăng nhập người dùng admin
        self.client.login(username='admin', password='password')

        # Kiểm tra với bộ lọc vai trò (role)
        response = self.client.get(reverse('user:export_users') + '?format=xlsx&role=Admin')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_export_users_no_role_permission(self):
        # Đăng nhập người dùng thường
        self.client.login(username='user', password='password')

        # Người dùng không có quyền xuất dữ liệu
        response = self.client.get(reverse('user:export_users') + '?format=xlsx')
        self.assertEqual(response.status_code, 302)  # Phải chuyển hướng
        self.assertRedirects(response, reverse('user:user_list'))

    def test_superuser_export(self):
        # Đăng nhập người dùng admin (siêu người dùng)
        self.client.login(username='admin', password='password')

        # Người dùng siêu người dùng có quyền xuất dữ liệu
        response = self.client.get(reverse('user:export_users') + '?format=xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_export_users_empty_role(self):
        # Đăng nhập người dùng admin
        self.client.login(username='admin', password='password')

        # Kiểm tra với vai trò trống (nên xuất tất cả người dùng trừ siêu người dùng)
        response = self.client.get(reverse('user:export_users') + '?format=xlsx&role=')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertGreater(len(response.content), 0)  # Kiểm tra file không rỗng



class ImportUsersViewTest(TestCase):
    def setUp(self):
        # Create superuser
        self.superuser = User.objects.create_superuser(username='admin', password='password', email='admin@example.com')

        # Create a regular user
        self.user = User.objects.create_user(username='testuser', password='password')
        role = Role.objects.create(role_name='Test Role')
        profile = Profile.objects.create(user=self.user, role=role)

        # Assign permission to the user's role
        self.permission = Permission.objects.get(codename='can_import_users')
        role.permissions.add(self.permission)

        self.role = role
        self.profile = profile

    def test_no_permission_access(self):
        # Login as user without permission
        self.client.login(username='testuser', password='password')

        # Remove permission to test access denied
        self.role.permissions.remove(self.permission)
        response = self.client.get(reverse('user:import_users'))

        # Check redirection and error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user:user_list'))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("You do not have permission to import user data." in str(msg) for msg in messages))

    def test_superuser_access(self):
        # Login as superuser
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('user:import_users'))

        # Check HTTP status
        self.assertEqual(response.status_code, 302)  # No POST request, so it will be blocked with the default message

    def test_import_valid_file(self):
        # Login as user with permission
        self.client.login(username='testuser', password='password')

        # Create a mock CSV file
        valid_file_content = "username,email\nuser1,test1@example.com\nuser2,test2@example.com"
        uploaded_file = SimpleUploadedFile("users.csv", valid_file_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post(reverse('user:import_users'), {'file': uploaded_file})

        # Check response
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user:user_list'))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Users have been successfully imported!" in str(msg) for msg in messages))

    def test_import_file_with_errors(self):
        # Login as user with permission
        self.client.login(username='testuser', password='password')

        # Create a mock CSV file with errors (for example, missing email)
        invalid_file_content = "username,email\nuser1,test1@example.com\nuser2,"  # Row 2 missing email
        uploaded_file = SimpleUploadedFile("users_with_errors.csv", invalid_file_content.encode('utf-8'), content_type="text/csv")

        # Perform POST request to import users
        response = self.client.post(reverse('user:import_users'), {'file': uploaded_file})

        # Capture messages after the redirect
        messages = list(response.wsgi_request._messages)

        # Debugging: Check the messages received
        print("Messages received:", [str(msg) for msg in messages])

        # Ensure the response is a redirect
        self.assertRedirects(response, reverse('user:user_list'))