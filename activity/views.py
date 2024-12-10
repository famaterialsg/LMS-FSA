from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserActivityLog
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import datetime as dt_timezone
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models.functions import TruncDate
import json 
import logging 
from openpyxl import Workbook, load_workbook
from .forms import ExcelImportForm
from django.conf import settings
from django.core.mail import send_mail


def monitor_activity_limit(request):
    user_activity_count = UserActivityLog.objects.filter(
        user=request.user,
        activity_timestamp__gte=timezone.now() - timezone.timedelta(minutes= 5)
    ).count()

    # Trigger an alert if activity count exceeds 30 within the time period
    if user_activity_count >= 30:
        send_mail(
            subject="Security Alert: High Activity Detected",
            message=f"User {request.user.username} has performed {user_activity_count} activities within the last 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
        )

@login_required
def activity_view(request):
    # monitor_activity_limit(request)
    
    # Get search and date filter parameters
    search_query = request.GET.get('search', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    # Get all activity logs for the user, ordered by newest first
    activity_logs = UserActivityLog.objects.filter(user=request.user).order_by('-activity_timestamp')

    # Log the activity if it's the first access or a search/filter is performed
    if not request.session.get('activity_page_accessed', False):
        UserActivityLog.objects.create(
            user=request.user,
            activity_type='page_visit',
            activity_details="Accessed activity_view",
            activity_timestamp=timezone.now()
        )
        request.session['activity_page_accessed'] = True

    if search_query or from_date or to_date:
        # Log the search/filter activity
        UserActivityLog.objects.create(
            user=request.user,
            activity_type='search',
            activity_details=f"Searched activities with query: '{search_query}' and dates: '{from_date}' to '{to_date}'",
            activity_timestamp=timezone.now()
        )

    # Filter activity logs based on search query and date range
    if search_query:
        activity_logs = activity_logs.filter(activity_details__icontains=search_query)
    date_format = "%y/%m/%d"
    if from_date:
        try:
            from_date_parsed = dt_timezone.strptime(from_date, date_format).date()
            activity_logs = activity_logs.filter(activity_timestamp__date__gte=from_date_parsed)
        except ValueError:
            pass  # Handle invalid date format or show an error message

    if to_date:
        try:
            to_date_parsed = dt_timezone.strptime(to_date, date_format).date()
            activity_logs = activity_logs.filter(activity_timestamp__date__lte=to_date_parsed)
        except ValueError:
            pass

    # Pagination setup
    page_number = request.GET.get('page', 1)
    page_size = 20
    paginator = Paginator(activity_logs, page_size)
    activity_logs_page = paginator.get_page(page_number)

    # Calculate the page range for pagination display
    page_range_start = max(activity_logs_page.number - 2, 1)
    page_range_end = min(activity_logs_page.number + 2, paginator.num_pages)
    page_range = range(page_range_start, page_range_end + 1)

    # Render the template with context data
    return render(request, 'activity.html', {
        'activity_logs': activity_logs_page,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
        'page_range': page_range,
    })

logger = logging.getLogger(__name__)

@login_required
def activity_dashboard_view(request):
    try:
        # Log only on the first GET request of the session
        if request.method == 'GET' and not request.session.get('activity_dashboard_accessed', False):
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='page_visit',
                activity_details="Accessed activity_dashboard_view",
                activity_timestamp=timezone.now()
            )
            # Set session flag to avoid logging on subsequent visits
            request.session['activity_dashboard_accessed'] = True

        # Retrieve activities for the current user
        activities = UserActivityLog.objects.filter(user=request.user)
        
        # Handle filters based on POST request data
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                from_date = data.get('from_date')
                to_date = data.get('to_date')
                view_type = data.get('view_type', 'activity_type')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        else:
            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')
            view_type = request.GET.get('view_type', 'activity_type')

        
        # Apply date filters if provided
        if from_date:
            try:
                from_date = dt_timezone.strptime(from_date, "%Y-%m-%d")
                activities = activities.filter(activity_timestamp__gte=from_date)
            except ValueError:
                logger.error(f"Invalid from_date format: {from_date}")

    
        if to_date:
            try:
                to_date = dt_timezone.strptime(to_date, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Invalid to_date format: {to_date}")
        else:
            # Set current day as to_date without timezone
            to_date = dt_timezone.now().replace(hour=23, minute=59, second=59)
            logger.info("to_date was None, set to current day")

        # Ensure to_date has the correct time even if parsed
        to_date = to_date.replace(hour=23, minute=59, second=59)

        activities = activities.filter(activity_timestamp__lte=to_date)

        print("come here")
        print(view_type)
        print(activities)
        # Process data based on view type
        if view_type == 'activity_details':
            recent_activities = activities.values('activity_details').annotate(count=Count('log_id'))
            recent_activities_labels = [activity['activity_details'] for activity in recent_activities]
            recent_activities_data = [activity['count'] for activity in recent_activities]
        else:  # Default to 'activity_type'
            recent_activities = activities.values('activity_type').annotate(count=Count('log_id'))
            recent_activities_labels = [activity['activity_type'] for activity in recent_activities]
            recent_activities_data = [activity['count'] for activity in recent_activities]

        # Activity over time data
        activity_over_time = (
            activities
            .annotate(date=TruncDate('activity_timestamp'))
            .values('date')
            .annotate(count=Count('log_id'))
            .order_by('date')
        )
        
        activity_over_time_labels = [entry['date'].strftime('%Y-%m-%d') for entry in activity_over_time]
        activity_over_time_data = [entry['count'] for entry in activity_over_time]

        response_data = {
            'total_activities': activities.count(),
            'recent_activities_labels': recent_activities_labels,
            'recent_activities_data': recent_activities_data,
            'activity_over_time_labels': activity_over_time_labels,
            'activity_over_time_data': activity_over_time_data,
        }

        # If POST request, return JSON response for filtering results
        if request.method == "POST":
            return JsonResponse(response_data)
        
        print("come herre")
        # For GET request, render the activity dashboard template
        return render(request, 'activity_dashboard.html', {
            **response_data,
            'view_type': view_type,
            'from_date': from_date.strftime('%Y-%m-%d') if isinstance(from_date, dt_timezone) else '',
            'to_date': to_date.strftime('%Y-%m-%d') if isinstance(to_date, dt_timezone) else '',
        })

    except Exception as e:
        logger.error(f"Error in activity_dashboard_view: {e}")
        if request.method == "POST":
            return JsonResponse({'error': str(e)}, status=500)
        return render(request, 'activity_dashboard.html', {
            'error': 'An error occurred while loading the dashboard.',
            'total_activities': 0,
            'recent_activities_labels': [],
            'recent_activities_data': [],
            'activity_over_time_labels': [],
            'activity_over_time_data': [],
        })
        

@login_required
def fetch_activity_logs(request):
    log_activity = request.GET.get('log_activity', 'false') == 'true'
    search_query = request.GET.get('search', '')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    page_number = request.GET.get('page', 1)  # Get the current page number from the query string

    activity_logs = UserActivityLog.objects.filter(user=request.user)

    if search_query:
        activity_logs = activity_logs.filter(activity_details__icontains=search_query)
    if from_date:
        activity_logs = activity_logs.filter(activity_timestamp__gte=parse_date(from_date))
    if to_date:
        activity_logs = activity_logs.filter(activity_timestamp__lte=parse_date(to_date))

    activity_logs = activity_logs.order_by('-activity_timestamp')

    # Pagination
    page_size = 20
    paginator = Paginator(activity_logs, page_size)
    activity_logs_page = paginator.get_page(page_number)

    # Paginated response
    data = [
        {
            'activity_type': log.get_activity_type_display(),
            'activity_details': log.activity_details,
            'activity_timestamp': timezone.localtime(log.activity_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        }
        for log in activity_logs_page
    ]

    # Pagination information
    pagination_info = {
        'has_previous': activity_logs_page.has_previous(),
        'has_next': activity_logs_page.has_next(),
        'current_page': activity_logs_page.number,
        'previous_page_number': activity_logs_page.previous_page_number() if activity_logs_page.has_previous() else None,
        'next_page_number': activity_logs_page.next_page_number() if activity_logs_page.has_next() else None,
        'page_range': list(paginator.page_range),
        'num_pages': paginator.num_pages,
    }

    if log_activity:
        UserActivityLog.objects.create(
            user=request.user,
            activity_type='fetch_activity_logs',
            activity_details='Fetched activity logs.',
            activity_timestamp=timezone.now()
        )

    response_data = {
        'logs': data,
        'pagination': pagination_info,
    }

    return JsonResponse(response_data)


@login_required
def export_data(request):
    # Get search, from_date, and to_date from GET parameters
    search_query = request.GET.get('search', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    # Base queryset for UserActivityLog
    queryset = UserActivityLog.objects.filter(user=request.user)

    # Apply search filter if a search query is provided
    if search_query:
        queryset = queryset.filter(
            Q(activity_type__icontains=search_query) |
            Q(activity_details__icontains=search_query)
        )

    # Apply date filters if 'from_date' and 'to_date' are provided
    if from_date:
        from_date_parsed = dt_timezone.strptime(from_date, '%Y-%m-%d')
        from_date_parsed = timezone.make_aware(from_date_parsed)  # Convert to timezone-aware datetime
        queryset = queryset.filter(activity_timestamp__gte=from_date_parsed)

    if to_date:
        to_date_parsed = dt_timezone.strptime(to_date, '%Y-%m-%d')
        to_date_parsed = timezone.make_aware(to_date_parsed)  # Convert to timezone-aware datetime
        queryset = queryset.filter(activity_timestamp__lte=to_date_parsed)

    # Check if queryset has results
    if queryset.exists():
        # Create an Excel workbook
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = 'Activity Logs'

        # Define headers for the Excel file
        headers = ['Activity Type', 'Details', 'Timestamp']
        worksheet.append(headers)

        # Populate rows with filtered data
        for log in queryset:
            timestamp = log.activity_timestamp.replace(tzinfo=None)  # Remove timezone for Excel compatibility
            row = [log.get_activity_type_display(), log.activity_details, timestamp]
            worksheet.append(row)

        # Construct the file name
        if from_date and to_date:
            file_name = f'activity_logs_{from_date}_to_{to_date}.xlsx'
        elif from_date:
            file_name = f'activity_logs_from_{from_date}.xlsx'
        elif to_date:
            file_name = f'activity_logs_until_{to_date}.xlsx'
        else:
            file_name = 'activity_logs.xlsx'

        # Set the response for file download
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        workbook.save(response)
        return response
    else:
        # If no data found, return an error message or empty response
        return HttpResponse('No data available for the given search and date filters.', status=404)

def tag_view(request):
    return render(request, 'tag.html')

