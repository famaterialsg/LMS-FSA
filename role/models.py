# role/models.py
from django.db import models
from module_group.models import Module
from django.core.exceptions import ValidationError

from django.db import models

class Role(models.Model):
    role_name = models.CharField(max_length=100, unique=True)
    is_protected = models.BooleanField(default=False)  # Đảm bảo role không thể bị xóa

    def save(self, *args, **kwargs):
        if self.is_protected and self.pk:  # Bảo vệ role khi đã được gắn cờ
            original = Role.objects.get(pk=self.pk)
            if not original.is_protected:
                raise ValueError("Cannot modify a protected role.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_protected:
            raise ValueError("Cannot delete a protected role.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.role_name

class RoleModule(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'module')  # Đảm bảo mỗi Role chỉ liên kết 1 Module 1 lần

    def __str__(self):
        return f"{self.role.role_name} - {self.module.module_name}"
