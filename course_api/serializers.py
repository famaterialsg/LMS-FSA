from rest_framework import serializers
from .models import *
from course.models import Course, Transaction, Topic, Tag, Session, CourseMaterial, ReadingMaterial, Enrollment, Completion, SessionCompletion, UserCourseProgress, MaterialViewingDuration

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'

class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        fields = '__all__'

class ReadingMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingMaterial
        fields = '__all__'

class CompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Completion
        fields = '__all__'

class SessionCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionCompletion
        fields = '__all__'

class UserCourseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCourseProgress
        fields = '__all__'

class MaterialViewingDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialViewingDuration
        fields = '__all__'
