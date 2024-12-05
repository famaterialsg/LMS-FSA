from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from .models import Department, Location
from .forms import DepartmentForm
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget
from user.models import User
from course.models import Course

class DepartmentResource(resources.ModelResource):
    users = fields.Field(
        column_name='users',
        attribute='users',
        widget=ManyToManyWidget(User, field='username', separator=',')
    )
    courses = fields.Field(
        column_name='courses',
        attribute='courses',
        widget=ManyToManyWidget(Course, field='course_name', separator=',')
    )
    location = fields.Field(
        column_name='location__name',
        attribute='location',
        widget=ForeignKeyWidget(Location, 'name')
    )
    address = fields.Field(
        column_name='address',
        attribute='location__address',
    )

    class Meta:
        model = Department
        skip_unchanged = True
        report_skipped = True
        fields = ('name', 'location', 'address', 'users', 'courses')
        import_id_fields = ()  # Không yêu cầu `name` là khóa duy nhất
        export_order = ('name', 'location', 'address', 'users', 'courses')

    def before_import_row(self, row, **kwargs):
        location_name = row['location__name']
        address = row.get('address', '')

        # Kiểm tra nếu location_name có tồn tại
        if not location_name:
            raise ValueError("Location name is required in the import file.")  # Nếu thiếu tên location

        # Sử dụng filter() thay vì get() để tránh lỗi nếu có nhiều địa điểm trùng tên
        locations = Location.objects.filter(name=location_name)

        if locations.exists():
            location = locations.first()  # Lấy đối tượng đầu tiên nếu có nhiều kết quả trùng tên
            if address and location.address != address:
                location.address = address
                location.save()
        else:
            # Nếu không tìm thấy, tạo mới Location
            location = Location.objects.create(name=location_name, address=address)

        row['location'] = location.id  # Cập nhật ID của Location vào row

    def skip_row(self, instance, original, row, import_validation, **kwargs):
        """
        So sánh dữ liệu mới và dữ liệu cũ, nếu tên Department và Location trùng nhau, bỏ qua dòng này.
        """
        # Kiểm tra nếu có một Department đã tồn tại với cùng tên và location
        if Department.objects.filter(name=instance.name, location=instance.location).exists():
            return True  # Bỏ qua dòng này nếu Department và Location trùng nhau

        return False

# Tạo DepartmentAdmin với tính năng ImportExport
class DepartmentAdmin(ImportExportModelAdmin):
    resource_class = DepartmentResource
    form = DepartmentForm
    list_display = ('name', 'get_location_name')

    def get_location_name(self, obj):
        return obj.location.name if obj.location else 'N/A'
    get_location_name.short_description = 'Location'

# Đăng ký các model vào admin
admin.site.register(Location)
admin.site.register(Department, DepartmentAdmin)
