from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from role.models import Role

User = get_user_model()

@receiver(post_save, sender=User)
def assign_staff_role(sender, instance, created, **kwargs):
    if created:
        # Tạo profile nếu chưa có
        if not hasattr(instance, "profile"):
            from user.models import Profile  # Tránh import vòng lặp
            Profile.objects.create(user=instance)

        # Gán role Super Admin nếu là staff user
        if instance.is_staff:  # Kiểm tra Staff status
            super_admin_role, _ = Role.objects.get_or_create(
                role_name="Super Admin", defaults={"is_protected": True}
            )
            instance.profile.role = super_admin_role
            instance.profile.save()
