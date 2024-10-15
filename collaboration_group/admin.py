from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import CollaborationGroup, GroupMember
from user.models import User
from subject.models import Subject  # Assuming Subject model is defined in yourapp.models

# CollaborationGroup Resource
class CollaborationGroupResource(resources.ModelResource):
    course = fields.Field(
        column_name='course__name',  # Assuming name is the desired attribute to import/export
        attribute='course',
        widget=ForeignKeyWidget(Subject, 'name')  # Use the name to link to the Subject model
    )
    created_by = fields.Field(
        column_name='created_by__username',  # Assuming username is the desired attribute to import/export
        attribute='created_by',
        widget=ForeignKeyWidget(User, 'username')  # Use the username to link to the User model
    )

    class Meta:
        model = CollaborationGroup
        fields = ('id', 'group_name', 'course', 'created_by', 'created_at')  # Add desired fields for import/export
        export_order = ('id', 'group_name', 'course', 'created_by', 'created_at')

# GroupMember Resource
class GroupMemberResource(resources.ModelResource):
    group = fields.Field(
        column_name='group__group_name',  # Assuming group_name is the desired attribute to import/export
        attribute='group',
        widget=ForeignKeyWidget(CollaborationGroup, 'group_name')  # Use group_name to link to CollaborationGroup
    )
    user = fields.Field(
        column_name='user__username',  # Assuming username is the desired attribute to import/export
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')  # Use the username to link to the User model
    )

    class Meta:
        model = GroupMember
        fields = ('id', 'group', 'user', 'joined_at')  # Add desired fields for import/export
        export_order = ('id', 'group', 'user', 'joined_at')

# Admin registration for CollaborationGroup
@admin.register(CollaborationGroup)
class CollaborationGroupAdmin(ImportExportModelAdmin):
    resource_class = CollaborationGroupResource
    list_display = ('group_name', 'course', 'created_by', 'created_at')
    search_fields = ('group_name', 'created_by__username', 'course__name')  # Add search fields
    list_filter = ('created_by', 'course')  # Filter options

# Admin registration for GroupMember
@admin.register(GroupMember)
class GroupMemberAdmin(ImportExportModelAdmin):
    resource_class = GroupMemberResource
    list_display = ('group', 'user', 'joined_at')
    search_fields = ('group__group_name', 'user__username')  # Add search fields
    list_filter = ('group', 'user')  # Filter options
