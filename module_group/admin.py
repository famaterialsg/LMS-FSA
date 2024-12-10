# admin.py

from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import ModuleGroup, Module

# Resource class for ModuleGroup
class ModuleGroupResource(resources.ModelResource):
    class Meta:
        model = ModuleGroup

# Resource class for Module
class ModuleResource(resources.ModelResource):
    class Meta:
        model = Module

# Register ModuleGroup with import/export functionality
@admin.register(ModuleGroup)
class ModuleGroupAdmin(ImportExportModelAdmin):
    resource_class = ModuleGroupResource
    list_display = ('group_name',)  # Customize the list display
    list_filter = ('group_name',)  # Thêm khả năng lọc theo nhóm

# Register Module with import/export functionality
@admin.register(Module)
class ModuleAdmin(ImportExportModelAdmin):
    resource_class = ModuleResource
    list_display = ('module_name', 'module_url', 'icon', 'module_group')  # Customize the list display
    list_filter = ('module_group',)  # Thêm khả năng lọc theo Module Group
    search_fields = ('module_name',)  # Tìm kiếm theo tên module