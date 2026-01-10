# apps/core/context_processors.py

from apps.agencies.models import Agency

def agency_branding(request):
    """
    Injeta branding da agência atual em todos os templates.
    """
    
    # Defaults (PostPro branding)
    defaults = {
        'agency': None,
        'agency_name': 'PostPro',
        'agency_logo_light': '/static/img/logo-light.png',
        'agency_logo_dark': '/static/img/logo-dark.png',
        'agency_logo_current': '/static/img/logo-light.png',
        'agency_favicon': '/static/img/favicon.ico',
        'agency_primary_color': '#FF6B35',
        'agency_secondary_color': '#004E89',
        'is_super_admin': False,
    }
    
    # 1. Unauthenticated or no agency
    if not request.user.is_authenticated:
        return defaults

    user = request.user
    
    # 2. Super Admin (Global view)
    if user.role == 'super_admin':
        defaults.update({
            'agency_name': 'PostPro (Admin)',
            'is_super_admin': True,
        })
        return defaults
    
    # 3. Agency User
    agency = getattr(user, 'agency', None)
    if not agency:
        return defaults
        
    # Detect theme from cookie
    current_theme = request.COOKIES.get('theme', 'light')
    
    return {
        'agency': agency,
        'agency_name': agency.get_display_name(),
        'agency_logo_light': agency.get_logo_url('light'),
        'agency_logo_dark': agency.get_logo_url('dark'),
        'agency_logo_current': agency.get_logo_url(current_theme),
        'agency_favicon': agency.get_favicon_url(),
        'agency_primary_color': agency.primary_color or '#FF6B35',
        'agency_secondary_color': agency.secondary_color or '#004E89',
        'is_super_admin': False,
    }
