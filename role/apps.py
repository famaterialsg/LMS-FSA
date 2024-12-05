# role/apps.py
from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class RoleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'role'

    def ready(self):
        from .models import Role  # Import cục bộ
        try:
            Role.objects.get_or_create(
                role_name="Super Admin", defaults={"is_protected": True}
            )
        except (OperationalError, ProgrammingError):
            # Bỏ qua lỗi nếu database chưa sẵn sàng
            pass

