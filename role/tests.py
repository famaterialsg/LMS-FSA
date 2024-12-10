from django.test import TestCase, Client
from django.urls import reverse
from module_group.models import ModuleGroup, Module
from role.models import Role, RoleModule
from user.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
import pandas as pd

class RoleViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Tạo người dùng superuser
        self.superuser = User.objects.create_superuser(username='admin', password='adminpass')
        self.client.login(username='admin', password='adminpass')

        # Tạo dữ liệu mẫu
        self.module_group = ModuleGroup.objects.create(group_name="Group 1")
        self.module_1 = Module.objects.create(module_name="Module 1", module_url="/module1/", module_group=self.module_group)
        self.module_2 = Module.objects.create(module_name="Module 2", module_url="/module2/", module_group=self.module_group)
        self.role = Role.objects.create(role_name="Test Role")
        RoleModule.objects.create(role=self.role, module=self.module_1)
        RoleModule.objects.create(role=self.role, module=self.module_2)

    def test_role_add_view(self):
        """Kiểm tra thêm một vai trò mới."""
        response = self.client.post(reverse('role:role_add'), {
            'role_name': 'New Role',
            'modules': [self.module_1.id, self.module_2.id],
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        new_role = Role.objects.get(role_name='New Role')
        self.assertTrue(RoleModule.objects.filter(role=new_role, module=self.module_1).exists())
        self.assertTrue(RoleModule.objects.filter(role=new_role, module=self.module_2).exists())

    def test_role_edit_view(self):
        """Kiểm tra chỉnh sửa một vai trò."""
        response = self.client.post(reverse('role:role_edit', args=[self.role.id]), {
            'role_name': 'Updated Role',
            'modules': [self.module_1.id],
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.role.refresh_from_db()
        self.assertEqual(self.role.role_name, 'Updated Role')
        self.assertEqual(self.role.rolemodule_set.count(), 1)
        self.assertTrue(RoleModule.objects.filter(role=self.role, module=self.module_1).exists())

    def test_role_delete_view(self):
        """Kiểm tra xóa một vai trò."""
        response = self.client.post(reverse('role:role_delete', args=[self.role.id]))
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertFalse(Role.objects.filter(id=self.role.id).exists())
        self.assertFalse(RoleModule.objects.filter(role=self.role).exists())

    def test_import_roles(self):
        """Kiểm tra chức năng import vai trò."""
        data = {
            'role_name': ['Role 1', 'Role 2'],
        }
        df = pd.DataFrame(data)
        xlsx_file = BytesIO()
        with pd.ExcelWriter(xlsx_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)

        xlsx_file.seek(0)
        uploaded_file = SimpleUploadedFile("roles.xlsx", xlsx_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response = self.client.post(reverse('role:import_roles'), {'file': uploaded_file})

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(Role.objects.filter(role_name='Role 1').exists())
        self.assertTrue(Role.objects.filter(role_name='Role 2').exists())

    def test_export_roles(self):
        """Kiểm tra chức năng export vai trò."""
        response = self.client.get(reverse('role:export_roles'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
