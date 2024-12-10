#add this into Middleware in settings.py (Ex:MIDDLEWARE = [
#    'django.middleware.security.SecurityMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
#   'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
#    'django.middleware.clickjacking.XFrameOptionsMiddleware',
#    'activity.activity_tracking_middleware.ActivityTrackingMiddleware',        add like this 
#])

# from django.utils import timezone
# from django.urls import resolve
# from .models import UserActivityLog

# class ActivityTrackingMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Process the request
#         response = self.get_response(request)

#         # Log activity if the user is authenticated and the request is GET
#         if request.user.is_authenticated and request.method == 'GET':
#             current_url = resolve(request.path_info).url_name
            
#             # Check if the user has already accessed the activity view
#             if current_url == 'activity_view':
#                 # Only log the activity if this is the first access during the session
#                 if not request.session.get('activity_page_accessed', False):
#                     UserActivityLog.objects.create(
#                         user=request.user,
#                         activity_type='page_visit',
#                         activity_details=f"Accessed {current_url}",
#                         activity_timestamp=timezone.now()
#                     )
#                     # Set the flag in the session to True
#                     request.session['activity_page_accessed'] = True
#             else:
#                 # For all other pages, log every access
#                 UserActivityLog.objects.create(
#                     user=request.user,
#                     activity_type='page_visit',
#                     activity_details=f"Accessed {current_url}",
#                     activity_timestamp=timezone.now()
#                 )

#                 # Reset the flag if they navigate away from the activity page
#                 if 'activity_page_accessed' in request.session:
#                     del request.session['activity_page_accessed']

#         return response
from django.utils import timezone
from django.urls import resolve
from .models import UserActivityLog
from course.models import Course

class ActivityTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)

        # Log activity if the user is authenticated and the request is GET
        if request.user.is_authenticated and request.method == 'GET':
            resolved_url = resolve(request.path_info)
            current_url = resolved_url.url_name

            # List of URLs to exclude from logging
            excluded_urls = ['unread_notification_count']  # Add any other URLs to exclude here

            if current_url not in excluded_urls:
                if current_url:
                    if'course' in current_url:
                        # Get the course ID from kwargs (from URL)
                        course_id = resolved_url.kwargs.get('pk')

                        if course_id:
                            try:
                                # Fetch course details from the database
                                course = Course.objects.get(pk=course_id)
                                activity_details = f"Accessed {current_url}: {course.course_name}"
                            except Course.DoesNotExist:
                                activity_details = "Accessed course page (course not found)"
                        else:
                            activity_details = f"Accessed {current_url}"

                        # Log course enrollment activity
                        UserActivityLog.objects.create(
                            user=request.user,
                            activity_type='page_visit',
                            activity_details=activity_details,
                            activity_timestamp=timezone.now()
                        )

                    elif current_url == 'activity_view':
                        # Only log the activity if this is the first access during the session
                        if not request.session.get('activity_page_accessed', False):
                            UserActivityLog.objects.create(
                                user=request.user,
                                activity_type='page_visit',
                                activity_details=f"Accessed {current_url}",
                                activity_timestamp=timezone.now()
                            )
                            # Set the flag in the session to True
                            request.session['activity_page_accessed'] = True
                    else:
                        # Log access to other pages
                        UserActivityLog.objects.create(
                            user=request.user,
                            activity_type='page_visit',
                            activity_details=f"Accessed {current_url}",
                            activity_timestamp=timezone.now()
                        )

                        # Reset the flag if they navigate away from the activity page
                        if 'activity_page_accessed' in request.session:
                            del request.session['activity_page_accessed']

        return response
