# yourapp/context_processors.py

from .models import Role

def user_roles(request):
    roles = Role.objects.all()
    temporary_role = request.session.get('temporary_role')
    return {
        'roles': roles,
        'temporary_role': temporary_role
    }
