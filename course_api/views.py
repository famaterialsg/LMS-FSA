from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import *
from course.models import Course, Transaction, Topic, Tag, Session, CourseMaterial, ReadingMaterial, Enrollment, Completion, SessionCompletion, UserCourseProgress, MaterialViewingDuration
from rest_framework.permissions import IsAuthenticated


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

class TopicViewSet(ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class SessionViewSet(ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

class EnrollmentViewSet(ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

class CourseMaterialViewSet(ModelViewSet):
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer

class ReadingMaterialViewSet(ModelViewSet):
    queryset = ReadingMaterial.objects.all()
    serializer_class = ReadingMaterialSerializer

class CompletionViewSet(ModelViewSet):
    queryset = Completion.objects.all()
    serializer_class = CompletionSerializer

class SessionCompletionViewSet(ModelViewSet):
    queryset = SessionCompletion.objects.all()
    serializer_class = SessionCompletionSerializer

class UserCourseProgressViewSet(ModelViewSet):
    queryset = UserCourseProgress.objects.all()
    serializer_class = UserCourseProgressSerializer

class MaterialViewingDurationViewSet(ModelViewSet):
    queryset = MaterialViewingDuration.objects.all()
    serializer_class = MaterialViewingDurationSerializer
