from module_group.models import Module, ModuleGroup
from role.models import Role

def get_grouped_modules(user, temporary_role_id=None):
    """
    Hàm lấy danh sách các module theo nhóm dựa trên role của người dùng.
    """
    all_modules = Module.objects.all()  # Lấy tất cả các modules
    user_modules = Module.objects.all()  # Mặc định không có modules nào

    if user.is_authenticated:
        if user.is_superuser or (user.profile.role and user.profile.role.role_name == "Manager"):
            # Nếu là superuser, kiểm tra role tạm thời
            if temporary_role_id:
                try:
                    temporary_role = Role.objects.get(role_name=temporary_role_id)
                    user_modules = all_modules.filter(rolemodule__role=temporary_role).distinct()
                except Role.DoesNotExist:
                    user_modules = Module.objects.none()
            else:
                user_modules = all_modules
        else:
            # Người dùng không phải superuser
            user_profile = getattr(user, 'profile', None)  # Giả định user có profile
            user_role = getattr(user_profile, 'role', None)  # Giả định profile có role
            if user_role:
                user_modules = all_modules.filter(rolemodule__role=user_role).distinct()
            else:
                user_modules = Module.objects.none()
    
    # Lấy danh sách các nhóm module
    module_groups = ModuleGroup.objects.all()
    grouped_modules = {}
    
    # Nhóm các module theo group
    for module in user_modules:
        group = module.module_group
        if group not in grouped_modules:
            grouped_modules[group] = []
        grouped_modules[group].append(module)
    
    return module_groups, grouped_modules
