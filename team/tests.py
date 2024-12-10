from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Member

class TeamViewsTestCase(TestCase):

    def setUp(self):
        # Tạo dữ liệu mẫu để sử dụng trong các test cases
        self.member1 = Member.objects.create(
            name="Nguyễn Văn A",
            role_member="Leader",
            email="a@example.com"
        )
        self.member2 = Member.objects.create(
            name="Trần Thị B",
            role_member="Manager",
            email="b@example.com"
        )

    def test_team_list_view(self):
        # Test hiển thị danh sách thành viên
        response = self.client.get(reverse('team:team_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.member1.name)
        self.assertContains(response, self.member2.name)

    def test_add_member_view(self):
        # Test thêm thành viên
        response = self.client.post(reverse('team:add_member'), {
            'name': 'Phạm Văn C',
            'role_member': 'Member',
            'email': 'c@example.com'
        })
        self.assertEqual(response.status_code, 302)  # Redirect sau khi thêm
        self.assertTrue(Member.objects.filter(name="Phạm Văn C").exists())

    def test_edit_member_view(self):
        # Test sửa thông tin thành viên
        response = self.client.post(reverse('team:edit_member', args=[self.member1.id]), {
            'name': 'Nguyễn Văn A Updated',
            'role_member': 'Leader',
            'email': 'updated@example.com'
        })
        self.assertEqual(response.status_code, 302)  # Redirect sau khi sửa
        self.member1.refresh_from_db()
        self.assertEqual(self.member1.name, 'Nguyễn Văn A Updated')
        self.assertEqual(self.member1.email, 'updated@example.com')

    def test_delete_member_view(self):
        # Test xóa thành viên
        response = self.client.post(reverse('team:delete_member', args=[self.member2.id]))
        self.assertEqual(response.status_code, 302)  # Redirect sau khi xóa
        self.assertFalse(Member.objects.filter(id=self.member2.id).exists())

    def test_search_member_view(self):
        # Test tìm kiếm thành viên theo tên
        response = self.client.get(reverse('team:team_list') + '?q=Nguyễn')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.member1.name)
        self.assertNotContains(response, self.member2.name)

    def test_export_members_view(self):
        # Test xuất danh sách thành viên
        response = self.client.get(reverse('team:export_members'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')