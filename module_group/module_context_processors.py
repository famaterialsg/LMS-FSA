from main.module_utils import get_grouped_modules  # Assuming this function is in utils.py
from role.context_processors import user_roles

def module_context(request):
    # Get roles and temporary role from the 'user_roles' context processor
    roles_context = user_roles(request)
    temporary_role = roles_context.get('temporary_role')  # Get the temporary role ID
    
    # Now, use the temporary_role and the user to fetch the modules
    module_groups, grouped_modules = get_grouped_modules(request.user, temporary_role)  # Get modules based on the user and temporary role
    
    # Return the context that will be added to the templates
    return {
        'module_groups': module_groups,
        'grouped_modules': grouped_modules
    }
