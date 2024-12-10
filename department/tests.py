from django.test import TestCase, Client
from django.urls import reverse
from user.models import User
from .models import Department, Location
from .forms import DepartmentForm
from django.contrib.messages import get_messages

class DepartmentTests(TestCase):
    def setUp(self):
        # Create a test client, user, and sample data
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.location = Location.objects.create(name="Test Location", address="123 Test Address")
        self.department = Department.objects.create(name="Test Department", location=self.location)

    def login(self):
        # Helper method to log in the test user
        self.client.login(username='testuser', password='password')

    def test_department_list_view(self):
        # Test department list view with pagination
        self.login()
        response = self.client.get(reverse('department:department_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'department_list.html')
        self.assertIn('page_obj', response.context)

    def test_department_detail_view(self):
        # Test department detail view
        self.login()
        response = self.client.get(reverse('department:department_detail', args=[self.department.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'department_detail.html')
        self.assertEqual(response.context['department'], self.department)

    def test_department_create_view(self):
        # Test creating a new department
        self.login()
        data = {'name': 'New Department', 'location': self.location.id}
        response = self.client.post(reverse('department:department_create'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect after creation
        self.assertTrue(Department.objects.filter(name="New Department").exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Phòng ban đã được thêm thành công!")

    def test_department_update_view(self):
        # Test updating an existing department
        self.login()
        data = {'name': 'Updated Department', 'location': self.location.id}
        response = self.client.post(reverse('department:department_update', args=[self.department.id]), data)
        self.assertEqual(response.status_code, 302)
        self.department.refresh_from_db()
        self.assertEqual(self.department.name, "Updated Department")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), f"Phòng ban {self.department.name} đã được cập nhật thành công.")

    def test_department_delete_view(self):
        # Test deleting a department
        self.login()
        response = self.client.post(reverse('department:department_delete'), {'selected_departments': [self.department.id]})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Department.objects.filter(id=self.department.id).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Selected departments have been deleted successfully.")

    def test_location_list_view(self):
        # Test location list view with pagination
        self.login()
        response = self.client.get(reverse('department:location_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'location_list.html')
        self.assertIn('page_obj', response.context)

    def test_export_departments_view(self):
        # Test exporting departments to file
        self.login()
        response = self.client.get(reverse('department:export_departments'), {'format': 'csv'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename=', response['Content-Disposition'])

    def test_import_departments_view_invalid_file(self):
        # Test importing departments with an invalid file format
        self.login()
        with open('test_file.invalid', 'w') as f:
            f.write("Invalid data")
        with open('test_file.invalid', 'rb') as f:
            response = self.client.post(reverse('department:import_departments'), {'file': f})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Định dạng tệp không hợp lệ. Hỗ trợ các định dạng: csv, json, yaml, tsv, xlsx.")