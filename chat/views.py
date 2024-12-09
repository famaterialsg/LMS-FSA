from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Max, Count, F, Min
from .models import Chat, User, GroupChat
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from module_group.models import ModuleGroup
from datetime import datetime
import json



def create_group_chat_view(request):
    if request.method == "POST":
        group_name = request.POST.get('group_name')  # Get group name from the form
        member_usernames = request.POST.getlist('members')  # List of selected usernames

        if group_name and member_usernames:
            # Create the group
            group = GroupChat.objects.create(name=group_name, created_by=request.user)

            # Add the selected members to the group
            for username in member_usernames:
                user = get_object_or_404(User, username=username)
                group.members.add(user)

            # Ensure the creator is also added to the group
            group.members.add(request.user)

            return redirect('chat:chat_view', group_id=group.id)

    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id)

    return render(request, 'chat/create_group_chat.html', {'users': users})

@login_required
def add_member_to_group_view(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    current_user = request.user

    # Ensure the current user is part of the group (either the creator or a member)
    if current_user not in group.members.all() and group.created_by != current_user:
        return redirect('some_error_page')  # Unauthorized access

    if request.method == "POST":
        member_usernames = request.POST.getlist('members')  # List of selected usernames

        # Add the selected members to the group
        for username in member_usernames:
            user = get_object_or_404(User, username=username)
            if user not in group.members.all():  # Avoid adding the same user again
                group.members.add(user)

        return redirect('chat:chat_view', group_id=group.id)

    # Get all users except those who are already in the group
    users = User.objects.exclude(id__in=group.members.all().values_list('id', flat=True))

    return render(request, 'chat/add_member_to_group.html', {'group': group, 'users': users})

@login_required
def remove_member_from_group_view(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    current_user = request.user

    # Ensure the current user is the creator of the group (only the creator can remove members)
    if group.created_by != current_user:
        return redirect('some_error_page')  # Unauthorized access

    if request.method == "POST":
        member_username = request.POST.get('member')  # Username of the member to remove
        member = get_object_or_404(User, username=member_username)

        if member != group.created_by:  # Prevent creator from removing themselves
            group.members.remove(member)

        return redirect('chat:chat_view', group_id=group.id)

    # Get all members of the group except the group creator
    members = group.members.exclude(id=group.created_by.id)

    return render(request, 'chat/remove_member_from_group.html', {'group': group, 'members': members})

@login_required
def edit_message_view(request, message_id):
    message = get_object_or_404(Chat, id=message_id, sender=request.user)
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                new_message = data.get('message', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON'})
            
            if new_message:
                message.message = new_message
                message.edited_at = timezone.now()
                message.save()
                return JsonResponse({
                    'success': True,
                    'message': message.message,
                    'edited_at': message.edited_at.strftime("%I:%M %p")
                })
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'})
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def delete_message_view(request, message_id):
    message = get_object_or_404(Chat, id=message_id, sender=request.user)
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            message.delete()
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def chat_view(request, username=None, group_id=None):
    current_user = request.user
    search_query = request.GET.get('q', '')
    message_search = request.GET.get('message_search', '')  # Add message search parameter

    # Filter users based on search query
    users = User.objects.exclude(id=current_user.id)
    if search_query:
        users = users.filter(username__icontains=search_query)

    group_chats = current_user.group_members.all()
    
    # Handle message sending
    if request.method == "POST":
        message_text = request.POST.get('message')
        if message_text:
            if group_id:
                group = get_object_or_404(GroupChat, id=group_id)
                if current_user in group.members.all():
                    Chat.objects.create(
                        sender=current_user,
                        group=group,
                        message=message_text
                    )
            elif username:
                receiver = get_object_or_404(User, username=username)
                Chat.objects.create(
                    sender=current_user,
                    receiver=receiver,
                    message=message_text
                )

    # Get unread messages count
    unread_count = Chat.objects.filter(
        receiver=current_user,
        is_read=False
    ).count()

    message_preview = (
        Chat.objects.filter(
            Q(receiver=current_user) | 
            Q(group__members=current_user)
        )
        .exclude(sender=current_user)
        .values(
            'sender__username',
            'group__name',
            'group_id',
            'message',
            'timestamp',
            'is_read'
        )
        .order_by('-timestamp')[:5]
        .annotate(
            message_content=F('message'),
            time_sent=F('timestamp'),
            sender_name=F('sender__username')
        )
    )

    # Process message previews
    for preview in message_preview:
        if preview['group__name']:
            preview['sender_name'] = f"{preview['sender__username']} in {preview['group__name']}"
        else:
            preview['sender_name'] = preview['sender__username']

    context = {
        'users': users,
        'group_chats': group_chats,
        'user': current_user,
        'unread_count': unread_count,
        'message_preview': message_preview,
        'search_query': search_query,
    }

    # Add chat-specific context
    if username:
        other_user = get_object_or_404(User, username=username)
        # Mark messages as read
        Chat.objects.filter(
            sender=other_user,
            receiver=current_user,
            is_read=False
        ).update(is_read=True)
        
        # Get messages
        messages = Chat.objects.filter(
            (Q(sender=current_user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=current_user))
        ).order_by('timestamp')
        
        context.update({
            'other_user': other_user,
            'messages': messages,
        })
    elif group_id:
        group = get_object_or_404(GroupChat, id=group_id)
        messages = Chat.objects.filter(group=group).order_by('timestamp')
        context.update({
            'group': group,
            'messages': messages,
        })

    return render(request, 'chat/chat_view.html', context)

@login_required
def message_report_view(request):
    current_user = request.user

    # Fetch report data
    report_data = (
        Chat.objects.filter(receiver=current_user)
        .values('sender__username')
        .annotate(
            latest_message=Max('timestamp'),
            message_count=Count('id'),
            unread_count=Count('id', filter=Q(is_read=False))
        )
        .order_by('-latest_message')
    )

    # Add message content and read status to the report data
    for data in report_data:
        latest_message = Chat.objects.filter(
            sender__username=data['sender__username'], 
            receiver=current_user
        ).order_by('-timestamp').first()

        data['message_content'] = latest_message.message if latest_message else "No message content"
        data['time_sent'] = latest_message.timestamp if latest_message else None
        data['is_read'] = latest_message.is_read if latest_message else True

    return render(request, 'chat/message_report.html', {'report_data': report_data})
