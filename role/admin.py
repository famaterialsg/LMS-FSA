from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Role, RoleModule
from module_group.models import Module

class RoleResource(resources.ModelResource):
    role_name = fields.Field(column_name='role_name', attribute='role_name')
    module_names = fields.Field(column_name='module_names')  # Loại bỏ widget ForeignKeyWidget

    class Meta:
        model = Role
        exclude = ('id',)
        fields = ('role_name', 'module_names')
        export_order = ('role_name', 'module_names')
        import_id_fields = ['role_name']
        skip_unchanged = True
        report_skipped = True

    def dehydrate_module_names(self, role):
        """Trích xuất danh sách Module liên kết với Role để export."""
        modules = RoleModule.objects.filter(role=role).select_related('module')
        return ", ".join([rm.module.module_name for rm in modules])

    def before_import_row(self, row, **kwargs):
        role_name = row.get('role_name')
        if role_name is None or not role_name.strip():
            raise ValueError("Thiếu hoặc không hợp lệ trường 'role_name' trong file import.")

        role_name = role_name.strip()

        # Tạo hoặc lấy Role
        role, created = Role.objects.get_or_create(role_name=role_name)

        # Xử lý danh sách module_names
        module_names = row.get('module_names', None)
        if module_names:
            # Kiểm tra nếu module_names không phải là None hoặc rỗng
            module_names = module_names.strip()
            module_names = [name.strip() for name in module_names.split(',') if name.strip()]
            for module_name in module_names:
                module, _ = Module.objects.get_or_create(module_name=module_name)
                RoleModule.objects.get_or_create(role=role, module=module)


class RoleModuleInline(admin.TabularInline):
    model = RoleModule
    extra = 1  # Số dòng trống để thêm mới
    verbose_name_plural = "Modules liên kết"
    autocomplete_fields = ['module']  # Bật tính năng tự động điền Module

@admin.register(Role)
class RoleAdmin(ImportExportModelAdmin):
    resource_class = RoleResource
    list_display = ('role_name', 'get_modules')  # Hiển thị các Module liên kết
    search_fields = ('role_name',)
    inlines = [RoleModuleInline]

    def get_modules(self, obj):
        """Hiển thị danh sách các Module liên kết với Role."""
        return ", ".join([rm.module.module_name for rm in RoleModule.objects.filter(role=obj)])
    get_modules.short_description = "Modules"


@admin.register(RoleModule)
class RoleModuleAdmin(admin.ModelAdmin):
    list_display = ('role', 'module')  # Hiển thị Role và Module
    search_fields = ('role__role_name', 'module__module_name')  # Tìm kiếm theo Role và Module
    list_filter = ('role', 'module')  # Bộ lọc Role và Module
    autocomplete_fields = ['role', 'module']  # Bật tính năng tự động điền