from django.db import models
from django.conf import settings

class Application(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)  # Name of the application
    description = models.TextField()  # Description of the application
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ApplicationSubmit(models.Model):
    id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='submissions')
    reason = models.TextField()  
    updated = models.DateTimeField(auto_now=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)

    def get_status(self):
        if self.approved and not self.declined:
            return "Approved"
        elif self.declined:
            return "Declined"
        else:
            return "Pending"
    
    def __str__(self):
        return f'{self.user.username} - {self.application.name}'