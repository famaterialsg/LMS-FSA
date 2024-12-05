from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'topics', TopicViewSet)
router.register(r'tags', TagViewSet)
router.register(r'sessions', SessionViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'course-materials', CourseMaterialViewSet)
router.register(r'reading-materials', ReadingMaterialViewSet)
router.register(r'completions', CompletionViewSet)
router.register(r'session-completions', SessionCompletionViewSet)
router.register(r'user-course-progress', UserCourseProgressViewSet)
router.register(r'material-viewing-duration', MaterialViewingDurationViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
