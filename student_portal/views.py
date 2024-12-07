# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from course.models import Course, Enrollment, Session, CourseMaterial, ReadingMaterial, Completion, SessionCompletion, Transaction, MaterialViewingDuration
from student_portal.models import RecommendedCourse
from django.contrib import messages
from feedback.models import CourseFeedback
import random
from django.utils import timezone  # for timestamp updates
from django.core.paginator import Paginator
from user.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import re
import urllib.parse
from django.conf import settings
import os
from django.core.files.storage import default_storage
import pdfplumber



def start_viewing(user, material, request):
    # Get the last viewed material URL and material ID from the session
    last_viewed_url = request.session.get('last_viewed_url', None)
    last_viewed_material = request.session.get('last_viewed_material', None)

    # Build the current material's URL
    current_url = request.build_absolute_uri()
    current_material_id = str(material.id)

    # Check if the current URL or material is different from the last viewed
    is_new_material = last_viewed_material != current_material_id
    is_new_url = last_viewed_url != current_url

    if is_new_material or is_new_url:
        # Create or update the MaterialViewingDuration entry
        viewing_duration, created = MaterialViewingDuration.objects.get_or_create(
            user=user,
            material=material,
            defaults={'start_time': timezone.now()}
        )

        if not created:
            # Update start time and increment come_back if a new view session
            viewing_duration.start_time = timezone.now()
            if is_new_material:
                viewing_duration.come_back += 1

        viewing_duration.save()

        # Update session tracking
        request.session['last_viewed_material'] = current_material_id
        request.session['last_viewed_url'] = current_url
    else:
        # Reload of the same material detected
        print("Page reload detected; no update to come_back or start time.")

def end_viewing(user, material):
    try:
        # Get the MaterialViewingDuration object
        viewing_duration = MaterialViewingDuration.objects.get(user=user, material=material)

        # Update the end_time
        viewing_duration.end_time = timezone.now()

        # Calculate the time spent on this viewing session
        if viewing_duration.start_time:
            time_spent_now = viewing_duration.end_time - viewing_duration.start_time

            # Add the new time spent to the total time_spent
            viewing_duration.time_spent += time_spent_now

        # Save the updated object
        viewing_duration.save()
    except MaterialViewingDuration.DoesNotExist:
        # Handle the case where the object does not exist
        pass


def end_viewing_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            material = get_object_or_404(CourseMaterial, id=material_id)
            end_viewing(request.user, material)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


def extract_course_content_url(url):
    # Regular expression to capture 'course/<course_id>/content' part of the URL
    match = re.search(r'/course/(\d+)/content', url)
    if match:
        return match.group(0)  # Returns the matched string '/course/<course_id>/content'
    return None  # Return None if no match is found


@login_required
def save_last_accessed_material(request):
    print(request.method)
    if request.method == 'POST':
        print("Started")
        data = json.loads(request.body)
        material_id = data.get('material_id')
        course_id = data.get('course_id')  # Get the course_id from the JSON data

        # Ensure that the course_id exists
        if not course_id:
            return JsonResponse({'success': False, 'error': 'Course ID is required'})

        try:
            enrollment = Enrollment.objects.get(student=request.user, course__pk=course_id)

            # Update the enrollment with the last accessed material
            material = CourseMaterial.objects.get(id=material_id)
            enrollment.last_accessed_material = material
            enrollment.save()
            return JsonResponse({'success': True})

        except CourseMaterial.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Material not found'})
        except Enrollment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Enrollment not found'})


@login_required
def course_content(request, pk, session_id):
    course = get_object_or_404(Course, pk=pk)
    sessions = Session.objects.filter(course=course).order_by('order')

    selected_session_id = request.POST.get('session_id') or session_id

    current_session = get_object_or_404(Session, id=selected_session_id)

    materials = CourseMaterial.objects.filter(session=current_session).order_by('order')

    enrollment = Enrollment.objects.get(student=request.user, course=course)

    file_id = request.GET.get('file_id')
    file_type = request.GET.get('file_type')
    if file_id and file_type:
        try:
            current_material = CourseMaterial.objects.get(id=file_id, material_type=file_type, session=current_session)
        except CourseMaterial.DoesNotExist:
            current_material = materials.first() if materials.exists() else None
    else:
        current_material = materials.first() if materials.exists() else None

    if current_material:
        start_viewing(request.user, current_material, request)

    # Increment come_back only if the user is not navigating between materials or reloading
    referer_url = request.META.get('HTTP_REFERER', '')
    current_url = request.build_absolute_uri()

    if f'student_portal/{pk}/content' not in referer_url:
        enrollment.come_back += 1
        enrollment.save()
    else:
        referer_course_url = extract_course_content_url(referer_url)
        current_course_url = extract_course_content_url(current_url)
        if referer_course_url != current_course_url:
            enrollment.come_back += 1
            enrollment.save()

    next_material = materials.filter(order__gt=current_material.order).first() if current_material else None
    next_session = None

    if not next_material and current_session:
        next_session = Session.objects.filter(course=course, order__gt=current_session.order).order_by('order').first()
        next_material = CourseMaterial.objects.filter(session=next_session).order_by(
            'order').first() if next_session else None

    # Determine content type and preview content
    content_type = None
    preview_content = None
    if current_material:
        reading = ReadingMaterial.objects.filter(material_id=current_material.id).first()
        if reading:
            preview_content = reading.content
            content_type = current_material.material_type

    # Completion status for the current material
    completion_status = (
        Completion.objects.filter(
            session=current_session,
            material=current_material,
            user=request.user,
            completed=True
        ).exists() if current_material else False
    )

    # Calculate course completion percentage
    total_materials = CourseMaterial.objects.filter(session__course=course).count()
    completed_materials = Completion.objects.filter(session__course=course, user=request.user, completed=True).count()
    completion_percent = (completed_materials / total_materials) * 100 if total_materials > 0 else 0

    # Check if user is eligible for a certificate
    total_sessions = sessions.count()
    completed_sessions = SessionCompletion.objects.filter(course=course, user=request.user, completed=True).count()
    certificate_url = (
        reverse('course:generate_certificate', kwargs={'pk': course.pk})
        if total_sessions > 0 and completed_sessions == total_sessions
        else None
    )

    context = {
        'course': course,
        'sessions': sessions,
        'current_session': current_session,
        'materials': materials,
        'current_material': current_material,
        'next_material': next_material,
        'content_type': content_type,
        'preview_content': preview_content,
        'completion_status': completion_status,
        'completion_percent': completion_percent,
        'certificate_url': certificate_url,
        'next_session': next_session,
    }

    return render(request, 'courses/course_content.html', context)


@require_POST
@login_required
def toggle_completion(request, pk):
    course = get_object_or_404(Course, pk=pk)
    file_id = request.POST.get('file_id')

    material = get_object_or_404(CourseMaterial, id=file_id, session__course=course)
    session = material.session

    completion, created = Completion.objects.get_or_create(
        session=session,
        material=material,
        user=request.user,
    )
    completion.completed = not completion.completed
    completion.save()

    # Check if all materials in the session are completed
    total_materials = session.materials.count()
    completed_materials = Completion.objects.filter(session=session, user=request.user, completed=True).count()
    session_completed = total_materials == completed_materials

    SessionCompletion.objects.update_or_create(
        user=request.user,
        session=session,
        course=course,
        defaults={'completed': session_completed}
    )

    # Find the next item
    next_material = CourseMaterial.objects.filter(
        session=session,
        order__gt=material.order
    ).order_by('order').first()

    next_session = None
    if not next_material:
        next_session = Session.objects.filter(course=course, order__gt=session.order).order_by('order').first()
        if next_session:
            next_material = CourseMaterial.objects.filter(session=next_session).order_by('order').first()

    next_item_type = next_material.material_type if next_material else None
    next_item_id = next_material.id if next_material else None
    next_session_id = next_session.id if next_session else None

    return JsonResponse({
        'completed': completion.completed,
        'next_item_type': next_item_type,
        'next_item_id': next_item_id,
        'next_session_id': next_session_id
    })


# @login_required
# def course_list(request):
#     # Retrieve all published courses initially
#     courses = Course.objects.filter(published=True)
#     query = request.GET.get('q')

#     # Fetch enrolled courses for the student
#     enrolled_courses = Enrollment.objects.filter(student=request.user).values_list('course', flat=True)
#     enrolled_courses_list = Course.objects.filter(id__in=enrolled_courses, published=True)

#     # If a search query is present, filter the courses based on the search
#     if query:
#         courses = courses.filter(Q(course_name__icontains=query) | Q(description__icontains=query))
#         enrolled_courses_list = enrolled_courses_list.filter(Q(course_name__icontains=query) | Q(description__icontains=query))

#     # Combine enrolled courses with other filtered courses, removing duplicates
#     courses = list(enrolled_courses_list) + [course for course in courses if course not in enrolled_courses_list]

#     # Add average rating to each course
#     for course in courses:
#         feedbacks = course.coursefeedback_set.all()
#         if feedbacks.exists():
#             total_ratings = sum(feedback.average_rating() for feedback in feedbacks)
#             course.average_rating = total_ratings / feedbacks.count()
#         else:
#             course.average_rating = 0.0  # Default to 0 if no feedbacks

#     # Insert or update recommended courses based on search results
#     for course in courses:
#         recommended_course, created = RecommendedCourse.objects.get_or_create(
#             course=course,
#             user=request.user,  # Associate with the logged-in user
#             defaults={'created_at': timezone.now()}
#         )
#         if not created:
#             recommended_course.created_at = timezone.now()
#             recommended_course.save()

#     # Pagination setup
#     paginator = Paginator(courses, 6)  # Show 6 courses per page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     # Get top recommended courses to display
#     recommended_courses = RecommendedCourse.objects.filter(course__published=True).order_by('-created_at')[:4]

#     # Render the course list with filtered and recommended courses
#     return render(request, 'courses/course_list.html', {
#         'courses': page_obj,
#         'recommended_courses': [rc.course for rc in recommended_courses],
#     })


def course_list(request):
    from collections import defaultdict

    # Retrieve all published courses
    courses = Course.objects.filter(published=True)
    query = request.GET.get('q')

    # Fetch enrolled courses for the student
    enrolled_course_ids = Enrollment.objects.filter(student=request.user).values_list('course', flat=True)
    enrolled_courses_list = Course.objects.filter(id__in=enrolled_course_ids, published=True)

    # If a search query is present, filter the courses
    if query:
        courses = courses.filter(Q(course_name__icontains=query) | Q(description__icontains=query))
        enrolled_courses_list = enrolled_courses_list.filter(
            Q(course_name__icontains=query) | Q(description__icontains=query))

    # Combine enrolled courses with other filtered courses, removing duplicates
    courses = list(enrolled_courses_list) + [course for course in courses if course not in enrolled_courses_list]
    courses = [course for course in courses if course.sessions.filter(materials__isnull=False).exists()]

    # Mark courses as enrolled or not, and process last accessed materials
    last_access_data = defaultdict(lambda: {"material": None, "session": None})

    for course in courses:
        course.user_enrolled = course.id in enrolled_course_ids

        # Get average rating for each course
        feedbacks = course.coursefeedback_set.all()
        if feedbacks.exists():
            total_ratings = sum(feedback.average_rating() for feedback in feedbacks)
            course.average_rating = total_ratings / feedbacks.count()
        else:
            course.average_rating = 0.0

        # Get last accessed material for the student if enrolled
        if course.user_enrolled:
            enrollment = Enrollment.objects.get(student=request.user, course=course)
            if enrollment.last_accessed_material:
                last_access_data[course.id] = {
                    "material": enrollment.last_accessed_material,
                    "session": enrollment.last_accessed_material.session,
                }
            else:
                # If no last accessed material, get the first session and its first material
                first_session = Session.objects.filter(course=course).first()
                if first_session and first_session.materials.exists():
                    last_access_data[course.id] = {
                        "material": first_session.materials.first(),
                        "session": first_session,
                    }
        else:
            first_session = Session.objects.filter(course=course).first()
            last_access_data[course.id] = {
                "material": first_session.materials.first(),
                "session": first_session,
            }

    # Pagination setup
    paginator = Paginator(courses, 6)  # Show 6 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get top recommended courses
    recommended_courses = RecommendedCourse.objects.filter(course__published=True).order_by('-created_at')[:4]

    # Render the course list with filtered and recommended courses
    return render(request, 'courses/course_list.html', {
        'courses': page_obj,
        'recommended_courses': [rc.course for rc in recommended_courses],
        'last_access_data': last_access_data,
    })


def count_words_in_pdf(pdf_path):
    word_count = 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract the text from the page
                text = page.extract_text()
                if text:
                    # Count words by splitting the text by whitespace
                    word_count += len(text.split())
    except Exception as e:
        print(f"Error processing PDF: {e}")
    return word_count

import urllib.parse
from googleapiclient.discovery import build

YOUTUBE_API_KEY = 'AIzaSyAzxLp14NgigkY99iNz684GG4iM4_lLfoI'


def get_youtube_video_duration(video_url):
    """
    Fetch the duration of a YouTube video using the YouTube Data API.

    Args:
        video_url (str): The YouTube video URL or embedded URL.

    Returns:
        int: Duration of the video in seconds, or 0 if the video cannot be fetched.
    """
    try:
        # Extract the video ID from the URL
        parsed_url = urllib.parse.urlparse(video_url)

        if "youtube.com/watch" in video_url:
            # Regular YouTube video link
            query_params = urllib.parse.parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]
        elif "youtube.com/embed/" in video_url:
            # Embedded YouTube video link
            path_parts = parsed_url.path.split('/')
            video_id = path_parts[-1] if path_parts else None
            # Remove query parameters from video ID if present
            if video_id and '?' in video_id:
                video_id = video_id.split('?')[0]
        else:
            video_id = None

        if not video_id:
            return 0

        # Initialize the YouTube API client
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        # Request video details
        response = youtube.videos().list(
            part='contentDetails',
            id=video_id
        ).execute()

        if 'items' in response and len(response['items']) > 0:
            content_details = response['items'][0]['contentDetails']
            duration_iso = content_details.get('duration')

            # Parse ISO 8601 duration into seconds
            return parse_iso8601_duration(duration_iso)

    except Exception as e:
        print(f"Error fetching video duration: {e}")

    return 0


def parse_iso8601_duration(duration_iso):
    """
    Convert ISO 8601 duration format (PnDTnHnMnS) to seconds.

    Args:
        duration_iso (str): Duration in ISO 8601 format (e.g., PT1H2M30S).

    Returns:
        int: Duration in seconds.
    """
    import isodate

    try:
        parsed_duration = isodate.parse_duration(duration_iso)
        return int(parsed_duration.total_seconds())
    except Exception as e:
        print(f"Error parsing ISO 8601 duration: {e}")
        return 0

@login_required
def course_detail(request, pk):
    # Get the course based on the primary key (pk)
    course = get_object_or_404(Course, pk=pk)

    # Check enrollment status
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    users_enrolled_count = Enrollment.objects.filter(course=course).count()

    # Get all feedback related to the course
    feedbacks = CourseFeedback.objects.filter(course=course)

    # Calculate the course's average rating
    if feedbacks.exists():
        total_rating = sum(feedback.average_rating() for feedback in feedbacks)
        course_average_rating = total_rating / feedbacks.count()
    else:
        course_average_rating = None  # No feedback yet

    course_average_rating_star = course_average_rating * 100 / 5 if course_average_rating is not None else 0

    # Get prerequisites
    prerequisites = course.prerequisites.all()

    # Get sessions
    sessions = Session.objects.filter(course=course)
    session_count = sessions.count()

    # Get random tags
    all_tags = list(course.tags.all())
    random_tags = random.sample(all_tags, min(4, len(all_tags)))

    # Fetch the latest feedbacks
    latest_feedbacks = feedbacks.order_by('-created_at')[:5]

    # Instructor info
    instructor = course.instructor
    is_instructor = Course.objects.filter(instructor=request.user).exists()
    user_type = 'instructor' if is_instructor else 'student'

    enrolled_users = Enrollment.objects.filter(course=course).select_related('student')

    # Calculate progress for each enrolled user
    user_progress = [
        {
            'user': enrollment.student,
            'progress': course.get_completion_percent(enrollment.student)
        }
        for enrollment in enrolled_users
    ]

    if is_enrolled:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        if enrollment:
            comeback = enrollment.come_back if enrollment.come_back else 0
            if enrollment.last_accessed_material:
                last_accessed_material = enrollment.last_accessed_material
                last_accessed_session = last_accessed_material.session
            else:
                last_accessed_session = sessions.first()
                if last_accessed_session and last_accessed_session.materials.exists():
                    last_accessed_material = last_accessed_session.materials.first()
                else:
                    last_accessed_material = None
        else:
            last_accessed_session = sessions.first()
            if last_accessed_session and last_accessed_session.materials.exists():
                last_accessed_material = last_accessed_session.materials.first()
            else:
                last_accessed_material = None
    else:
        comeback = 0
        last_accessed_session = sessions.first()
        if last_accessed_session and last_accessed_session.materials.exists():
            last_accessed_material = last_accessed_session.materials.first()
        else:
            last_accessed_material = None

    articles = []
    exercises = []
    lectures_list = []
    total_duration = []
    youtube_total_duration = 0

    # Loop through each session
    for session in sessions:
        # Get all the materials for this session in one query
        materials = CourseMaterial.objects.filter(session=session,
                                                  material_type__in=['lectures', 'references', 'assignments', 'labs',
                                                                     'assessments'])

        # Loop through all materials in this session
        for material in materials:
            #material.expect_duration = 0
            # Append to articles or exercises list based on material type
            if material.material_type in ['lectures', 'references']:
                articles.append(material)
            elif material.material_type in ['assignments', 'labs', 'assessments']:
                exercises.append(material)

            # If it's a lecture, add it to the lectures list
            if material.material_type == 'lectures':
                lectures_list.append(material)

            # Calculate the expected duration for the material
            reading = ReadingMaterial.objects.get(id=material.material_id)
            if reading.content:
                youtube_links = re.findall(
                    r'(https?://(?:www\.)?youtube\.com/(?:watch\?v=[\w-]+|embed/[\w-]+)(?:\?[\w=&-]*)?)',
                    reading.content)
                print("This is the link:", youtube_links, "of the reading number", reading.title)
                for link in youtube_links:
                    youtube_total_duration += get_youtube_video_duration(link)
                    #material.expect_duration += get_youtube_video_duration(link)
                    print("This is the total duration:", youtube_total_duration)

                match = re.search(r'src="(/media/course_pdf/.*?)"', reading.content)
                if match:
                    file_url = match.group(1)  # Extract the URL part from the 'src' attribute
                    decoded_file_url = urllib.parse.unquote(file_url)  # Decode the URL
                    decoded_file_url = decoded_file_url.split('#')[0]
                    file_path = decoded_file_url.lstrip('/media')  # Remove leading slash to get the actual file path
                    file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    if default_storage.exists(file_path):
                        word_count = count_words_in_pdf(file_path)
                        material.expect_duration = word_count / 250
                    else:
                        print(f"File does not exist: {file_path}")
                else:
                    plain_text = re.sub(r'<[^>]+>', '', reading.content)
                    word_count = len(plain_text.split())
                    material.expect_duration = word_count / 250

                material.save()

            # Add to total duration list for later summing
            total_duration.append(material.expect_duration)

        # Calculate and store the lecture count for the session
        session.lecture_count = len([m for m in materials if m.material_type == 'lectures'])

    youtube_duration_hours = youtube_total_duration / 3600

    context = {
        'course': course,
        'prerequisites': prerequisites,
        'is_enrolled': is_enrolled,
        'users_enrolled_count': users_enrolled_count,
        'course_average_rating_star': course_average_rating_star,
        'course_average_rating': course_average_rating,
        'feedbacks': feedbacks,
        'sessions': sessions,
        'session_count': session_count,
        'latest_feedbacks': latest_feedbacks,
        'tags': course.tags.all() if course.tags else [],
        'instructor': instructor,
        'user_type': user_type,
        'user_progress': user_progress,
        'random_tags': random_tags,
        'comeback': comeback,
        'last_accessed_material': last_accessed_material,
        'last_accessed_session': last_accessed_session,
        'articles_count': len(articles),
        'exercises_count': len(exercises),
        'lectures_list': len(lectures_list),
        'total_duration': sum(total_duration)/60 + youtube_duration_hours,
        'youtube_duration': youtube_duration_hours,
    }

    return render(request, 'courses/course_detail.html', context)


@login_required
def course_content2(request, pk):
    print('come here')

    # Retrieve the course by primary key
    course = get_object_or_404(Course, pk=pk)
    print(course)

    print('ab=')
    # Retrieve all sessions for this course, ordered by 'order'
    sessions = Session.objects.filter(course=course)

    print(sessions)
    # Attempt to get `session_id` from POST; if not present, it's set to None
    selected_session_id = request.POST.get('session_id') or None

    # Determine the current session based on `session_id` or default to the first session
    if selected_session_id:
        # If session_id is provided, try to retrieve the session
        current_session = get_object_or_404(Session, id=selected_session_id, course=course)
    else:
        # If no session_id is provided, default to the first session in the list
        current_session = sessions.first() if sessions.exists() else None

    # If there is no current session (e.g., no sessions found), handle this case appropriately
    if current_session is None:
        # Redirect to an error page or show a message if needed
        return render(request, 'courses/error.html', {'message': 'No sessions available for this course.'})

    # Retrieve course materials for the current session
    materials = CourseMaterial.objects.filter(session=current_session).order_by('order')

    file_id = request.GET.get('file_id')
    file_type = request.GET.get('file_type')
    current_material = None
    if file_id and file_type:
        try:
            current_material = CourseMaterial.objects.get(id=file_id, material_type=file_type, session=current_session)
        except CourseMaterial.DoesNotExist:
            current_material = materials.first() if materials.exists() else None
    else:
        current_material = materials.first() if materials.exists() else None

    next_material = materials.filter(order__gt=current_material.order).first() if current_material else None
    next_session = None

    if not next_material:
        next_session = Session.objects.filter(course=course, order__gt=current_session.order).order_by('order').first()
        if next_session:
            next_material = CourseMaterial.objects.filter(session=next_session).order_by('order').first()

    content_type = None
    preview_content = None

    if current_material:
        if current_material.material_type == 'assignments':
            reading = ReadingMaterial.objects.get(material_id=current_material.id)
            preview_content = reading.content
            content_type = 'assignments'
        elif current_material.material_type == 'labs':
            reading = ReadingMaterial.objects.get(material_id=current_material.id)
            preview_content = reading.content
            content_type = 'labs'
        elif current_material.material_type == 'lectures':
            reading = ReadingMaterial.objects.get(material_id=current_material.id)
            preview_content = reading.content
            content_type = 'lectures'
        elif current_material.material_type == 'references':
            reading = ReadingMaterial.objects.get(material_id=current_material.id)
            preview_content = reading.content
            content_type = 'references'

    completion_status = Completion.objects.filter(
        session=current_session,
        material=current_material,
        user=request.user,
        completed=True
    ).exists() if current_material else False

    total_materials = CourseMaterial.objects.filter(session__course=course).count()
    completed_materials = Completion.objects.filter(
        session__course=course,
        user=request.user,
        completed=True
    ).count()
    completion_percent = (completed_materials / total_materials) * 100 if total_materials > 0 else 0

    total_sessions = sessions.count()
    completed_sessions = SessionCompletion.objects.filter(course=course, user=request.user, completed=True).count()

    certificate_url = None
    if total_sessions > 0 and completed_sessions == total_sessions:
        # Call the function to generate the certificate URL
        certificate_url = reverse('courses:generate_certificate', kwargs={'pk': course.pk})

    context = {
        'course': course,
        'sessions': sessions,
        'current_session': current_session,
        'materials': materials,
        'current_material': current_material,
        'next_material': next_material,
        'content_type': content_type,
        'preview_content': preview_content,
        'completion_status': completion_status,
        'completion_percent': completion_percent,
        'certificate_url': certificate_url,
        'next_session': next_session,
    }

    return render(request, 'courses/course_content.html', context)


@login_required
def instructor_profile(request, instructor_id):
    # Get the instructor based on the instructor ID
    instructor = get_object_or_404(User, id=instructor_id)

    # Get courses taught by this instructor
    courses = Course.objects.filter(instructor=instructor)

    # Get feedback for each course to calculate average ratings
    for course in courses:
        feedbacks = CourseFeedback.objects.filter(course=course)
        if feedbacks.exists():
            total_rating = sum(feedback.average_rating() for feedback in feedbacks)
            course.average_rating = total_rating / feedbacks.count()
        else:
            course.average_rating = None  # No feedback yet

    context = {
        'instructor': instructor,
        'courses': courses,
    }

    return render(request, 'instructor_profile.html', context)


@login_required
def enroll(request, pk):
    course = get_object_or_404(Course, id=pk)
    if course.published == True and course.instructor is not None:
        Enrollment.objects.update_or_create(student=request.user, course=course, defaults={'is_active': True, 'date_enrolled': timezone.now()})
        messages.success(request, f"You have successfully enrolled in {course.course_name}.")
    else:
        messages.error(request, f"{course.course_name} is not ready to be enrolled.")
    return redirect('student_portal:course_detail', pk=course.id)


@login_required
def unenroll(request, pk):
    # Get the course based on the primary key (pk)
    course = get_object_or_404(Course, pk=pk)

    # Attempt to delete the enrollment for the current user
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()

    if enrollment:
        enrollment.delete()
        messages.success(request, f"You have successfully unenrolled from {course.course_name}.")
    else:
        messages.warning(request, f"You are not enrolled in {course.course_name}.")

    return redirect('student_portal:course_detail', pk=course.pk)