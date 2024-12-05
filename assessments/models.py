from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from course.models import Course
from exercises.models import Exercise
from quiz.models import Question, AnswerOption
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Sum
from user.models import User

from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver

    
class AssessmentType(models.Model):
    type_name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Assessment Type"
        verbose_name_plural = "Assessment Types"

    def __str__(self):
        return self.type_name
    def save(self, *args, **kwargs):
        # Check for duplicates
        if AssessmentType.objects.filter(type_name=self.type_name).exists():
            raise ValidationError(_("This assessment type already exists."))
        super().save(*args, **kwargs)


class Assessment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE,related_name='assessments')  # This line ensures a course reference
    
    title = models.CharField(max_length=255)
    
    # Many-to-many relationships
    exercises = models.ManyToManyField(Exercise, related_name='assessments', blank=True)
    questions = models.ManyToManyField(Question, related_name='assessments', blank=True)

    # Foreign key to AssessmentType
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE, related_name='assessments')

    invited_count = models.IntegerField(default=0, verbose_name="Invited Count")
    assessed_count = models.IntegerField(default=0, verbose_name="Assessed Count")
    qualified_count = models.IntegerField(default=0, verbose_name="Qualified Count") 

    qualify_score = models.IntegerField(default=60, verbose_name="Qualify Score")
    total_score = models.IntegerField(default=100, verbose_name="Total Score")
    
    created_at = models.DateTimeField(default=timezone.now)
    # due_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_assessments')

    time_limit = models.IntegerField(default=30)
    invited_emails = models.TextField(blank=True, verbose_name="Invited Candidates")
    
    #Weights for the assessment
    assessment_weights = models.FloatField(default=1.0, verbose_name="Weights")
    ass_weights= models.FloatField(default=0.5, blank=True,null=True)
    quiz_weights =models.FloatField(default=0.5,null=True,blank=True)
    
    class Meta:
        ordering = ['created_at', 'course']
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"

    def __str__(self):
        return f"{self.title} ({self.assessment_type})"

    def is_past_due(self):
        """Check if the due date has passed."""
        return self.due_date and timezone.now() > self.due_date

    def invite_candidates(self):
        """Send invitations to all invited candidates."""
        candidates = self.invited_candidates.split(',')
        for email in candidates:
            email = email.strip()
            if email:  # Check if email is not empty
                send_mail(
                    'You are Invited to an Assessment',
                    f'You have been invited to participate in the assessment: {self.title}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

class InvitedCandidate(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='invited_candidates_list')
    email = models.EmailField()
    invitation_date = models.DateTimeField(auto_now_add=True)  # Automatically set when the candidate is invited
    expiration_date = models.DateTimeField(null=True, blank=True)  # Can be null until set

    def save(self, *args, **kwargs):
        # Call set_expiration_date before saving the instance
        self.set_expiration_date()
        super().save(*args, **kwargs)

    def set_expiration_date(self, days=7):
        """
        Set the expiration date based on the invitation date and number of days.
        Default is 7 days.
        """
        if self.invitation_date:
            self.expiration_date = self.invitation_date + timedelta(days=days)
        else:
            self.expiration_date = timezone.now() + timedelta(days=days)

    def __str__(self):
        return f"Invited Candidate: {self.email} for {self.assessment.title}"
    
class UserAnswer(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # selected_option = models.ForeignKey(AnswerOption, on_delete=models.SET_NULL, null=True, blank=True)
    selected_options = models.ManyToManyField(AnswerOption, blank=True)
    text_response = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Answer for {self.question} in {self.assessment}"

class StudentAssessmentAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")  # Optional email for anonymous users
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)

    # Scoring and feedback
    score_quiz = models.IntegerField(default=0, verbose_name="Quiz Score")
    score_ass = models.IntegerField(default=0, verbose_name="Assignment Score")
    
    note = models.TextField(blank=True, null=True, verbose_name="Notes")

    # Additional fields to track user answers and submissions
    user_answers = models.ManyToManyField(UserAnswer, related_name='attempts', blank=True)
    user_submissions = models.ManyToManyField('exercises.Submission', related_name='attempts', blank=True)

    is_proctored = models.BooleanField(default=False)
    proctoring_data = models.JSONField(null=True,blank=True, default=dict)
    
    # Timestamps and User relations
    attempt_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Student Assignment Attempt"
        verbose_name_plural = "Student Assignmenint Attempts"

    def __str__(self):
        user_info = self.user.username if self.user else self.email  # Display user or email
        return f"Attempt by {user_info} for {self.assessment}"

    def clean(self):
        # Ensure both scores are non-negative
        if self.score_quiz < 0:
            raise ValidationError({'score_quiz': _("Quiz score cannot be negative.")})
        if self.score_ass < 0:
            raise ValidationError({'score_ass': _("Assignment score cannot be negative.")})
        if not self.user and not self.email:
            raise ValidationError(_('Either user or email must be provided.'))

    def save(self, *args, **kwargs):
        # Clean data before saving
        self.clean()
        super().save(*args, **kwargs)

class AssessmentFinalScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")  # Optional email for anonymous users
    assessment =models.ForeignKey(Assessment,on_delete=models.CASCADE)
    final_score_ass = models.FloatField(default=0)
    final_score_quiz =models.FloatField(default=0)
    final_score = models.FloatField(default=0)
    
    
    def update_score(self):

        
            highest_score_ass = StudentAssessmentAttempt.objects.filter(
                user=self.user, assessment = self.assessment
            ).annotate(
                highest_score=F('score_ass'),
                
            ).order_by('-highest_score').first()

            highest_score_quiz =StudentAssessmentAttempt.objects.filter(
                user=self.user, assessment = self.assessment
            ).annotate(
                highest_score=F('score_quiz'),
                
            ).order_by('-highest_score').first()

            try:
                self.final_score_ass= highest_score_ass.score_ass * highest_score_ass.assessment.ass_weights 
                self.final_score_quiz= highest_score_quiz.score_quiz * highest_score_quiz.assessment.quiz_weights
                self.final_score = (self.final_score_ass + self.final_score_quiz)* self.assessment.assessment_weights
                
                
            except AttributeError:
                self.final_score_ass=0
                self.final_score_quiz=0
                self.final_score=0
                
            self.save()
    class Meta:
        verbose_name = 'Student Assessment Score'
        verbose_name_plural ='Student Assessment Score'
        db_table ='student_assessment_score'

@receiver([post_save,post_delete],sender = StudentAssessmentAttempt)
def update_assessment(sender, instance, **kwargs):
        final,created = AssessmentFinalScore.objects.get_or_create(
            user = instance.user,
            assessment = instance.assessment
        )
        final.update_score()



class CourseFinalScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")  # Optional email for anonymous users
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    score = models.FloatField(blank=True,null=True)
    date = models.DateField(auto_now_add=True,null=True,blank=True)

    def final_score(self):
        final_score = AssessmentFinalScore.objects.filter(
            user=self.user,
            assessment__course = self.course
        ).aggregate(
            final_score=models.Sum('final_score')
        )['final_score']
        self.score = final_score or 0
        self.date = timezone.now()
        self.save()

    class Meta:
        verbose_name = 'Course Final Score'
        verbose_name_plural ='Course Final Scores'
        db_table ='course_final_score'

@receiver([post_save,post_delete],sender = AssessmentFinalScore)
def update_course(sender, instance, **kwargs):
    final,created = CourseFinalScore.objects.get_or_create(
        user = instance.user,
        course = instance.assessment.course
    )
    final.final_score()

    




    

        
        
    

    
        
