from django.db import models
from user.models import User
from course.models import Course
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from quiz.models import StudentQuizAttempt
from certification.models import Certification
from course.models import Course, Enrollment
from assessments.models import Assessment, StudentAssessmentAttempt


class ProgressNotification(models.Model):    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    notification_message = models.CharField(max_length=255, blank=True, null=True)
    notification_date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)


@receiver(post_save, sender=Certification)
def create_progress_notification_certificate(sender, instance, **kwargs):
    message = f"Congratulations, Certificate is Ready!"
    
    ProgressNotification.objects.update_or_create(
        user=instance.user,
        course=instance.course,  
        notification_message=message
    )

@receiver(post_save, sender=Enrollment)
def create_progress_notification_on_enrollment(sender, instance, **kwargs):
    message = f"Welcome to course {instance.course}!"

    ProgressNotification.objects.update_or_create(
        user=instance.student,
        course=instance.course,
        notification_message=message
    )

@receiver(post_delete, sender=Enrollment)
def delete_progress_notification_on_enrollment(sender, instance, **kwargs):
    ProgressNotification.objects.filter(
        user=instance.student,
        course=instance.course,
    ).delete()

@receiver(post_save, sender=StudentAssessmentAttempt)
def create_progress_notification_on_assessment_attempt(sender, instance, **kwargs):
    try:
        message = f"You completed the assessment with a Quiz Score: {instance.score_quiz} and an Assignment Score: {instance.score_ass}!"

        ProgressNotification.objects.create(
            user=instance.user,
            course=instance.assessment.course,
            notification_message = message
        )
    except: pass