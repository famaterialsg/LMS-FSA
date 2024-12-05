from django.test import TestCase
from user.models import User
from course.models import Course, Enrollment 
from assessments.models import CourseFinalScore 
from achievement.models import PerformanceAnalytics

# class PerformanceAnalyticsTestCase(TestCase):
#     def setUp(self):
#         self.user = User.objects.create(username='testuser')
#         self.course = Course.objects.create(course_name='Test Course')
#         self.enrollment = Enrollment.objects.create(student=self.user, course=self.course)
#         self.course_final_score = CourseFinalScore.objects.create(user=self.user, course=self.course, score=95.0)

#     def test_create_performance_analytics(self):
#         performance = PerformanceAnalytics.objects.get(user=self.user, course=self.course)
#         self.assertIsNotNone(performance)
#         self.assertEqual(performance.user, self.user)
#         self.assertEqual(performance.course, self.course)

#     def test_update_performance_analytics(self):
#         performance = PerformanceAnalytics.objects.get(user=self.user, course=self.course)
#         self.course_final_score.score = 100.0
#         self.course_final_score.save()
#         performance.refresh_from_db()
#         self.assertEqual(performance.score, 100.0)

#     def test_delete_performance_analytics(self):
#         self.enrollment.delete()
#         with self.assertRaises(PerformanceAnalytics.DoesNotExist):
#             PerformanceAnalytics.objects.get(user=self.user, course=self.course)

#     def test_signal_update_on_course_final_score_save(self):
#         self.course_final_score.score = 90.0
#         self.course_final_score.save()
#         performance = PerformanceAnalytics.objects.get(user=self.user, course=self.course)
#         self.assertEqual(performance.score, 90.0)

#     def test_signal_update_on_course_save(self):
#         self.course.course_name = 'Updated Course'
#         self.course.save()
#         performance = PerformanceAnalytics.objects.get(user=self.user, course=self.course)
#         self.assertEqual(performance.course.course_name, 'Updated Course')

#     def test_signal_create_on_enrollment_save(self):
#         new_user = User.objects.create(username='newuser')
#         new_course = Course.objects.create(course_name='New Course')
#         new_enrollment = Enrollment.objects.create(student=new_user, course=new_course)
#         performance = PerformanceAnalytics.objects.get(user=new_user, course=new_course)
#         self.assertIsNotNone(performance)

#     def test_signal_delete_on_enrollment_delete(self):
#         new_user = User.objects.create(username='newuser')
#         new_course = Course.objects.create(course_name='New Course')
#         new_enrollment = Enrollment.objects.create(student=new_user, course=new_course)
#         new_enrollment.delete()
#         with self.assertRaises(PerformanceAnalytics.DoesNotExist):
#             PerformanceAnalytics.objects.get(user=new_user, course=new_course)
# from django.test import TestCase
# from user.models import User
# from .models import AIInsights
# from assessments.models import StudentAssessmentAttempt, Assessment, AssessmentType
# from course.models import Course, Enrollment
# from django.db import IntegrityError

# class AIInsightsModelTest(TestCase):

#     def setUp(self):
#         self.user = User.objects.create_user(username='testuser', password='testpassword')
#         self.course = Course.objects.create(course_name="Test Course", description="Test Course Description")
#         self.assessment_type = AssessmentType.objects.create(type_name="Type 1")
#         self.assessment = Assessment.objects.create(
#         course=self.course,
#         created_by=self.user,
#         assessment_type=self.assessment_type
#     )

#     def test_create_aiinsight(self):
#         insight = AIInsights.objects.create(
#             user=self.user,
#             course=self.course,
#             insight_text="This is a test insight.",
#             insight_type="Positive"
#         )

#         self.assertEqual(insight.user, self.user)
#         self.assertEqual(insight.course, self.course)
#         self.assertEqual(insight.insight_text, "This is a test insight.")
#         self.assertEqual(insight.insight_type, "Positive")


#     def test_update_or_create_on_enrollment_save(self):
#         enrollment = Enrollment.objects.create(student=self.user, course=self.course)
        
#         insight = AIInsights.objects.get(user=self.user, course=self.course)
#         self.assertIsNotNone(insight)
#         self.assertEqual(insight.insight_text, None)
#         self.assertEqual(insight.insight_type, None)

#     def test_delete_on_enrollment_delete(self):
#         enrollment = Enrollment.objects.create(student=self.user, course=self.course)
#         enrollment.delete()

#         with self.assertRaises(AIInsights.DoesNotExist):
#             AIInsights.objects.get(user=self.user, course=self.course)



from django.test import TestCase
from django.contrib.auth import get_user_model
from achievement.models import UserProgress
from course.models import Course
from django.utils.timezone import now
from decimal import Decimal
from assessments.models import Assessment, StudentAssessmentAttempt, AssessmentType
from unittest.mock import patch, Mock
from django.db.models.signals import post_save
User = get_user_model()

class UserProgressModelTest(TestCase):
    def setUp(self):
        # Tạo dữ liệu mẫu cho test
        self.user = User.objects.create_user(email="testuser@example.com", password="password123", username='testuser')
        self.admin = User.objects.create_superuser(username='tranleduy',password='123@123')
        self.course = Course.objects.create(course_code="COURSE101", course_name="Introduction to Testing")
        self.assessment = Assessment.objects.create(title="Test Assessment", 
                                                    total_score=100, 
                                                    course = self.course, 
                                                    created_by = self.admin,
                                                    assessment_type = AssessmentType.objects.create(type_name='Assignment'))
        self.attempt = StudentAssessmentAttempt.objects.create(
            user=self.user, assessment=self.assessment, score_ass=60
        )
        self.enrollment = Enrollment.objects.create(student=self.user, course=self.course)

    def test_create_user_progress(self):
        # Kiểm tra có thể tạo đối tượng UserProgress
        UserProgress.objects.filter(user=self.user, course=self.course).delete()
        progress = UserProgress.objects.create(user=self.user, course=self.course, progress_percentage=50.25)
        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.course, self.course)
        self.assertEqual(progress.progress_percentage, Decimal("50.25"))

    def test_unique_together_constraint(self):
        # Kiểm tra ràng buộc unique_together
        UserProgress.objects.filter(user=self.user, course=self.course).delete()
        UserProgress.objects.create(user=self.user, course=self.course, progress_percentage=10.00)
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            UserProgress.objects.create(user=self.user, course=self.course, progress_percentage=20.00)

    def test_default_progress_percentage(self):
        # Kiểm tra giá trị mặc định của progress_percentage
        UserProgress.objects.filter(user=self.user, course=self.course).delete()
        progress = UserProgress.objects.create(user=self.user, course=self.course)
        self.assertEqual(progress.progress_percentage, Decimal("0"))

    def test_last_accessed_field_updates(self):
        # Kiểm tra last_accessed được cập nhật tự động
        UserProgress.objects.filter(user=self.user, course=self.course).delete()
        progress = UserProgress.objects.create(user=self.user, course=self.course)
        initial_last_accessed = progress.last_accessed
        progress.progress_percentage = 75.00
        progress.save()
        self.assertNotEqual(progress.last_accessed, initial_last_accessed)
        self.assertGreater(progress.last_accessed, initial_last_accessed)

    def test_post_save_assessment(self):
        UserProgress.objects.filter(user=self.user, course=self.course).delete()
        self.assessment.save()
        progress = UserProgress.objects.filter(course=self.assessment.course).exists()
        self.assertTrue(progress)

    def tes_post_save_studentAttemptAssessment(self):
        UserProgress.objects.filter(user=self.user, course=self.course).delete()
        self.attempt.save()
        progress = UserProgress.objects.filter(course=self.assessment.course).exists()
        self.assertTrue(progress)

    def test_post_delete_studentAttemptAssessment(self):
        UserProgress.objects.filter(user=self.user, course=self.course).delete()
        self.attempt.delete()
        progress = UserProgress.objects.filter(course=self.assessment.course).exists()
        self.assertTrue(progress)