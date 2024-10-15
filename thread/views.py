from django.shortcuts import render, get_object_or_404, redirect
from .models import DiscussionThread, ThreadComments, ThreadReaction, CommentReaction
from .forms import ThreadForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from course.models import Course
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

# Thread List
@login_required
def thread_list(request, course_id=None):
    q = request.GET.get('q', '')

    if course_id:
        threads = DiscussionThread.objects.filter(
            Q(thread_title__icontains=q) |
            Q(thread_content__icontains=q) |
            Q(created_by__username__icontains=q),
            course_id=course_id
        )
    else:
        threads = DiscussionThread.objects.filter(
            Q(thread_title__icontains=q) |
            Q(thread_content__icontains=q) |
            Q(created_by__username__icontains=q)
        )
     # Apply pagination
    paginator = Paginator(threads, 10)  # 10 threads per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    courses = Course.objects.all()

    context = {
        'threads': threads,
        'courses': courses,
        'query': q,
    }
    return render(request, 'thread/thread_list.html', context)


# Create Thread
@login_required
def createThread(request):
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.created_by = request.user
            thread.save()
            return redirect('thread:thread_list')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = ThreadForm()

    return render(request, 'thread/thread_form.html', {'form': form})


# Update Thread
@login_required
def updateThread(request, pk):
    thread = get_object_or_404(DiscussionThread, pk=pk)

    if request.user != thread.created_by and not request.user.is_superuser:
        return redirect('thread:thread_list')

    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            return redirect('thread:thread_list')
    else:
        form = ThreadForm(instance=thread)

    return render(request, 'thread/thread_form.html', {'form': form})


# Delete Thread
@login_required
def deleteThread(request, pk):
    thread = get_object_or_404(DiscussionThread, pk=pk)

    if request.user != thread.created_by and not request.user.is_superuser:
        return redirect('thread:thread_list')

    if request.method == 'POST':
        thread.delete()
        return redirect('thread:thread_list')

    return render(request, 'thread/thread_confirm_delete.html', {'thread': thread})



def thread_detail(request, pk):
    # Get the thread object or return 404 if it doesn't exist
    thread = get_object_or_404(DiscussionThread, pk=pk)
    
    # Get the likes and loves counts for the thread
    likes_count = ThreadReaction.objects.filter(thread=thread, reaction_type='like').count()
    loves_count = ThreadReaction.objects.filter(thread=thread, reaction_type='love').count()
    
    # Prepare a list to hold comments with their reaction counts
    comments_with_reactions = []
    for comment in thread.comments.all():
        # Get likes and loves counts for each comment
        comment_likes_count = CommentReaction.objects.filter(comment=comment, reaction_type='like').count()
        comment_loves_count = CommentReaction.objects.filter(comment=comment, reaction_type='love').count()
        
        # Append the comment and its reaction counts to the list
        comments_with_reactions.append({
            'comment': comment,
            'likes_count': comment_likes_count,
            'loves_count': comment_loves_count,
        })
    
    # Prepare context data for the template
    context = {
        'thread': thread,
        'likes_count': likes_count,
        'loves_count': loves_count,
        'comments_with_reactions': comments_with_reactions,
    }
    
    # Render the template with the context data
    return render(request, 'thread/thread_detail.html', context)


# Add Comment
@login_required
def add_comment(request, pk):
    thread = get_object_or_404(DiscussionThread, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.thread = thread
            comment.user = request.user
            comment.save()
            return redirect('thread:thread_detail', pk=thread.pk)
    else:
        form = CommentForm()

    comments = thread.comments.all()
    return render(request, 'thread/thread_detail.html', {'thread': thread, 'comments': comments, 'form': form})


# Update Comment
@login_required
def update_comment(request, pk, comment_id):
    comment = get_object_or_404(ThreadComments, pk=comment_id)

    if request.user != comment.user and not request.user.is_superuser:
        return redirect('thread:thread_detail', pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('thread:thread_detail', pk=pk)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'thread/comment_form.html', {'form': form, 'comment': comment})


# Delete Comment
@login_required
def delete_comment(request, pk, comment_id):
    thread = get_object_or_404(DiscussionThread, pk=pk)
    comment = get_object_or_404(ThreadComments, pk=comment_id, thread=thread)

    if request.user != comment.user and not request.user.is_superuser:
        return redirect('thread:thread_detail', pk=thread.pk)

    if request.method == 'POST':
        comment.delete()
        return redirect('thread:thread_detail', pk=thread.pk)

    return render(request, 'thread/comment_confirm_delete.html', {'comment': comment})


# Add Reaction to Thread
@login_required
def add_reaction_to_thread(request, pk, reaction_type):
    thread = get_object_or_404(DiscussionThread, pk=pk)

    reaction, created = ThreadReaction.objects.get_or_create(
        user=request.user,
        thread=thread,
        defaults={'reaction_type': reaction_type}
    )

    if not created:
        reaction.reaction_type = reaction_type
        reaction.save()

    return redirect('thread:thread_detail', pk=pk)


# Add Reaction to Comment
@login_required
def add_reaction_to_comment(request, comment_id, reaction_type):
    comment = get_object_or_404(ThreadComments, pk=comment_id)

    reaction, created = CommentReaction.objects.get_or_create(
        user=request.user,
        comment=comment,
        defaults={'reaction_type': reaction_type}
    )

    if not created:
        reaction.reaction_type = reaction_type
        reaction.save()

    return redirect('thread:thread_detail', pk=comment.thread.pk)


def moderation_warning(request):
    return render(request, 'thread/moderation_warning.html')

@require_POST
def react_to_thread(request, thread_id):
    reaction_type = request.POST.get('reaction_type')
    thread = get_object_or_404(DiscussionThread, pk=thread_id)

    # Check if the user has already reacted
    existing_reaction = ThreadReaction.objects.filter(user=request.user, thread=thread)

    if existing_reaction.exists():
        # Update existing reaction
        existing_reaction.update(reaction_type=reaction_type)
    else:
        # Create new reaction
        ThreadReaction.objects.create(user=request.user, thread=thread, reaction_type=reaction_type)

    # Calculate new counts
    likes_count = ThreadReaction.objects.filter(thread=thread, reaction_type='like').count()
    loves_count = ThreadReaction.objects.filter(thread=thread, reaction_type='love').count()

    # Redirect back to the thread detail page with updated counts
    return redirect('thread:thread_detail', pk=thread.pk)

@require_POST
def react_to_comment(request, comment_id):
    reaction_type = request.POST.get('reaction_type')
    comment = get_object_or_404(ThreadComments, pk=comment_id)

    # Check if the user has already reacted
    existing_reaction = CommentReaction.objects.filter(user=request.user, comment=comment)

    if existing_reaction.exists():
        # Update existing reaction
        existing_reaction.update(reaction_type=reaction_type)
    else:
        # Create new reaction
        CommentReaction.objects.create(user=request.user, comment=comment, reaction_type=reaction_type)

    # Calculate new counts
    likes_count = CommentReaction.objects.filter(comment=comment, reaction_type='like').count()
    loves_count = CommentReaction.objects.filter(comment=comment, reaction_type='love').count()

    # Redirect back to the thread detail page
    return redirect('thread:thread_detail', pk=comment.thread.pk)