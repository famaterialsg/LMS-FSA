from django.shortcuts import render, redirect, get_object_or_404
from .models import ApplicationSubmit
from .forms import ApplicationCreateForm, ApplicationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.db.models import Q
from datetime import datetime


app_name = 'Application'


def filter_applications(queryset, search_query='', start_date='', end_date=''):
    """Applies search and date filters to a queryset of applications."""
    if search_query:
        queryset = queryset.filter(
            Q(application__name__icontains=search_query) | Q(reason__icontains=search_query)
        )
    if start_date:
        from_date_parsed = parse_date(start_date)
        if from_date_parsed:
            queryset = queryset.filter(updated__gte=from_date_parsed)
    if end_date:
        to_date_parsed = parse_date(end_date)
        if to_date_parsed:
            to_date_with_time = datetime.combine(to_date_parsed, datetime.max.time())
            queryset = queryset.filter(updated__lte=to_date_with_time)
    return queryset


@login_required
def application_home_view(request):
    return render(request, 'application_home.html')


@login_required
def application_submit_view(request):
    """Allows regular users to submit applications."""
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.created_by = request.user
            application.save()
            return redirect('Application:user_application_list')
    else:
        form = ApplicationForm()
    return render(request, 'application_add.html', {'form': form})


@user_passes_test(lambda user: user.is_superuser)
@login_required
def application_add_view(request):
    """Allows superusers to add new applications to the system."""
    if request.method == 'POST':
        form = ApplicationCreateForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.created_by = request.user
            application.save()
            return redirect('Application:application_home')
    else:
        form = ApplicationCreateForm()
    return render(request, 'application_add.html', {'form': form})


@login_required
def user_application_list_view(request):
    """Displays applications submitted by the logged-in user with search and date filters."""
    applications_list = ApplicationSubmit.objects.filter(created_by=request.user).order_by('-updated')

    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Apply filters using helper function
    applications_list = filter_applications(applications_list, search_query, start_date, end_date)

    paginator = Paginator(applications_list, 10)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)

    context = {
        'applications': applications,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'user_application_list.html', context)


@login_required
def application_edit_view(request, application_id):
    """Allows the user to edit their own application."""
    application = get_object_or_404(ApplicationSubmit, id=application_id)
    if request.user != application.created_by:
        return HttpResponseForbidden("You are not allowed to edit this application.")

    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            return redirect('Application:user_application_list')
    else:
        form = ApplicationForm(instance=application)
    return render(request, 'application_edit.html', {'form': form, 'application': application})


@login_required
def application_delete_view(request, application_id):
    """Allows the user to delete their own application."""
    application = get_object_or_404(ApplicationSubmit, id=application_id)
    if request.user != application.created_by:
        return HttpResponseForbidden("You are not allowed to delete this application.")

    if request.method == 'POST':
        application.delete()
        return redirect('Application:user_application_list')
    return render(request, 'application_confirm_delete.html', {'application': application})


@user_passes_test(lambda user: user.is_superuser)
@login_required
def manage_applications_view(request):
    """Allows superusers to view, search, and filter all applications with options to approve or decline."""
    applications_list = ApplicationSubmit.objects.all().order_by('-updated')

    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Apply filters using helper function
    applications_list = filter_applications(applications_list, search_query, start_date, end_date)

    paginator = Paginator(applications_list, 10)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)

    # Handle approve/decline actions
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        action = request.POST.get('action')
        application = get_object_or_404(ApplicationSubmit, id=application_id)

        if action == 'approve':
            application.approved = True
            application.declined = False
        elif action == 'decline':
            application.approved = False
            application.declined = True

        application.save()

    context = {
        'applications': applications,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'manage_applications.html', context)
