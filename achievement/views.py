from django.shortcuts import render
from module_group.models import ModuleGroup, Module
from course.models import Course
from django.core.paginator import Paginator
from .models import UserProgress, PerformanceAnalytics, AIInsights
import json
from .forms import AI_InsightsCourseForm, UserProgressForm, AIInsightsFilterForm
from assessments.models import StudentAssessmentAttempt, Assessment
from user.models import User
# Create your views here.
module_groups = ModuleGroup.objects.all()
modules = Module.objects.all()

# def user_progress(request):

#     module_groups = ModuleGroup.objects.all()
#     modules = Module.objects.all()
    
#     progress = UserProgress.objects.filter(user = request.user)
#     completed = UserProgress.objects.filter(user=request.user, progress_percentage=100).count()

#     percent_complete = round((completed / progress.count())*100,2) if progress.count() > 0 else 0

#     paginator_pro = Paginator(progress, 3) 

#     page_number_pro = request.GET.get('page')
#     page_obj_pro = paginator_pro.get_page(page_number_pro)

#     return render(request,'user_progress.html',{'module_groups': module_groups,
#                                              'modules': modules,
#                                              'courses': page_obj_pro,
#                                              'course_count':progress.count(),
#                                              'completed': completed,
#                                              'percent_complete':percent_complete,
#                                              'user': request.user ,
#                                              'page_obj_pro':page_obj_pro})

def user_progress(request):
###################################### For Admin #############################################
    if request.user.is_superuser:
        all_user =  users = User.objects.all()
        form = UserProgressForm(request.GET) 
        # Variable for tab My Progress
        admin_user = request.user
        admin_course_count = UserProgress.objects.filter(user = request.user).count()
        admin_completed = UserProgress.objects.filter(user=request.user, progress_percentage=100).count()
        admin_percent_complete = round((admin_completed / admin_course_count)*100,2) if admin_course_count > 0 else 0
        admin_paginator_pro = Paginator(UserProgress.objects.filter(user = request.user), 2)
        admin_page_number_pro = request.GET.get('page')
        admin_page_obj_pro = admin_paginator_pro.get_page(admin_page_number_pro)

        admin_progress = {
            'admin_user': admin_user,
            'admin_course_count': admin_course_count,
            'admin_completed': admin_completed,
            'admin_percent_complete': admin_percent_complete,
            'admin_course': admin_page_obj_pro,
            'admin_page_obj_pro':admin_page_obj_pro
        }

        if not form.is_valid():
            message = 'Please select User'
            return render(request, 'user_progress_admin.html', {'module_groups': module_groups,
                                                           'modules': modules,
                                                           'form':form,
                                                           'users':all_user,
                                                           'message':message,
                                                           'admin_progress':admin_progress})
        else:
    
            username = form.data['search_user']
            users = User.objects.filter(username = username)
            if users.count() == 0:
                message  = 'Not Found User'
                return render(request, 'user_progress_admin.html', {'module_groups': module_groups,
                                                           'modules': modules,
                                                           'form':form,
                                                           'users':all_user,
                                                           'message':message,
                                                           'admin_progress':admin_progress})
            else: 
                message = None
                
                progress = UserProgress.objects.filter(user=users[0])
                completed = UserProgress.objects.filter(user=users[0], progress_percentage=100).count()
                percent_complete = round((completed / progress.count())*100,2) if progress.count() > 0 else 0
                paginator_pro = Paginator(progress, 2) 
                page_number_pro = request.GET.get('page')
                page_obj_pro = paginator_pro.get_page(page_number_pro)

                return render(request, 'user_progress_admin.html', {'module_groups': module_groups,
                                                            'modules': modules,
                                                            'form':form,
                                                            'users':all_user,
                                                            'message':message,
                                                            'percent_complete':percent_complete,
                                                            'courses': page_obj_pro,
                                                            'course_count':progress.count(),
                                                            'completed': completed,
                                                            'search_user':users[0],
                                                            'page_obj_pro':page_obj_pro,
                                                            'admin_progress':admin_progress})
    
###################################### For User #############################################
    else:
        progress = UserProgress.objects.filter(user = request.user)
        completed = UserProgress.objects.filter(user=request.user, progress_percentage=100).count()

        percent_complete = round((completed / progress.count())*100,2) if progress.count() > 0 else 0

        paginator_pro = Paginator(progress, 3) 

        page_number_pro = request.GET.get('page')
        page_obj_pro = paginator_pro.get_page(page_number_pro)

        return render(request,'user_progress.html',{'module_groups': module_groups,
                                                'modules': modules,
                                                'courses': page_obj_pro,
                                                'course_count':progress.count(),
                                                'completed': completed,
                                                'percent_complete':percent_complete,
                                                'user': request.user ,
                                                'page_obj_pro':page_obj_pro})


def performance_analytics(request):
    user = request.user  
    analytics = PerformanceAnalytics.objects.filter(user=user.id)
    # Annotate each PerformanceAnalytics object with total assessments and qualified attempts
    # Annotate each PerformanceAnalytics object with total assessments and qualified attempts
    for data in analytics:
        data.total_assessments = Assessment.objects.filter(course=data.course).count()
        data.qualified_attempts = 0
        assessments = Assessment.objects.filter(course=data.course)
        for data in analytics:
            data.total_assessments = Assessment.objects.filter(course=data.course).count()
            data.qualified_attempts = 0
            data.attempts = []
            assessments = Assessment.objects.filter(course=data.course)
            for assessment in assessments:
                qualifying_score = assessment.qualify_score
                qualified_attempts = StudentAssessmentAttempt.objects.filter(
                    user=data.user,
                    assessment=assessment,
                    score_ass__gte=qualifying_score
                ).values('assessment').distinct().count()
                data.qualified_attempts += qualified_attempts
                data.attempts.extend(StudentAssessmentAttempt.objects.filter(
                    user=data.user,
                    assessment=assessment,
                    # score_ass__gte=qualifying_score
                ))
            
    paginator = Paginator(analytics,4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj':page_obj,
        'module_groups': module_groups,
        'modules': modules,
    }
    return render(request, 'performance_analytics.html', context)


def ai_insights(request):
    user = request.user 
    form = AIInsightsFilterForm(request.GET)
    chart_name = []

    ai_insights = AIInsights.objects.all()
    if form.is_valid() and form.data.getlist('courses'):  # Sử dụng getlist() để lấy danh sách
        course_ids = form.data.getlist('courses')  # Lấy danh sách các ID khóa học đã chọn

        # Lọc AI Insights cho các khóa học được chọn
        ai_insights = AIInsights.objects.filter(
            user=user.id,
            course__in=course_ids  
        ).order_by('-created_at')

        course_names = Course.objects.filter(id__in=course_ids).values_list('course_name', flat=True)  
        chart_name = list(course_names)
        is_valid = True
    else:
        course_id = request.GET.get('course')  # Use the GET parameter for course
        if course_id:
            ai_insights = AIInsights.objects.filter(user=user.id, course=course_id).order_by('-created_at')
            course = Course.objects.get(id=course_id).course_name
            chart_name = course
            is_valid = True
        else:
            ai_insights = AIInsights.objects.filter(user=user.id).order_by('-created_at')
            chart_name = ['All courses']
            is_valid = False

    labels = ['Good', 'Improvement', 'Worsening', 'Try Harder', 'Bad', 'Other']
    color = ['#00b627', '#2196F3', '#FFD700', '#FFA500', '#ff2c2c', '#535353']
    dict_color = dict(zip(labels, color))
    ai_insights_count = ai_insights.count()

    # Filter insights by type and count them
    counts = {label.lower(): ai_insights.filter(insight_type__iexact=label).count() for label in labels[:-1]}
    other_count = ai_insights_count - sum(counts.values())
    data = [counts['good'], counts['improvement'], counts['worsening'], counts['try harder'], counts['bad'], other_count]

    paginator = Paginator(ai_insights, 4)  # Show 10 insights per page
    page_number = request.GET.get('page')  # Get the page number from the URL
    page_obj = paginator.get_page(page_number)

    # Prepare query parameters to keep form values on page change
    query_params = request.GET.copy()  # Make a copy of the GET parameters
    if 'page' in query_params:
        del query_params['page']  # Remove the current page parameter if it exists
    chart_name = ', '.join(chart_name)

    return render(request, 'ai_insights.html', {
        'form': form,
        'page_obj': page_obj,
        'query_params': query_params,
        'chart_name':chart_name,
        'user': request.user,
        'data': data,
        'labels': labels,
        'chart_name': chart_name,
        'is_valid': is_valid,
        'dict_color': dict_color,
        'color': color
    })
