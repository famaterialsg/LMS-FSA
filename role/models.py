from django.db import models
from module_group.models import Module

class Role(models.Model):
    role_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.role_name


class RoleModule(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'module')  # Đảm bảo mỗi Role chỉ liên kết 1 Module 1 lần

    def __str__(self):
        return f"{self.role.role_name} - {self.module.module_name}"
