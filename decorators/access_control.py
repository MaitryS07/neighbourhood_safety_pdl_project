from functools import wraps
from flask import flash, redirect, url_for, session, request
from flask_login import current_user, login_required as flask_login_required


def login_required(f):
    """
    Enhanced login required decorator that stores the intended URL
    and provides user-friendly error messages.
    """
    @wraps(f)
    @flask_login_required  # Use Flask-Login's decorator
    def decorated_function(*args, **kwargs):
        # User is authenticated by Flask-Login, so we can proceed
        return f(*args, **kwargs)

    # Store the intended URL in session for redirect after login
    if request.endpoint and request.endpoint != 'auth.login':
        session['next'] = request.url if request.method == 'GET' else request.referrer

    return decorated_function


def admin_required(f):
    """
    Decorator that requires user to be authenticated and have admin role.
    Redirects residents to resident dashboard with appropriate message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))

        # Check if user has admin role
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('resident.dashboard'))

        return f(*args, **kwargs)

    return decorated_function


def resident_required(f):
    """
    Decorator that requires user to be authenticated.
    Both residents and admins can access resident pages.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))

        # Both admin and resident can access resident pages
        return f(*args, **kwargs)

    return decorated_function


def logout_required(f):
    """
    Decorator that ensures user is not authenticated.
    Redirects authenticated users to appropriate dashboard.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            # Redirect to appropriate dashboard based on user role
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('resident.dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def self_or_admin_required(user_id_param='user_id'):
    """
    Decorator that allows access only if:
    - User is admin, OR
    - User is accessing their own data

    Usage: @self_or_admin_required('user_id') where user_id is the route parameter
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))

            # Admin can access any data
            if current_user.is_admin():
                return f(*args, **kwargs)

            # Check if user is accessing their own data
            target_user_id = kwargs.get(user_id_param)
            if target_user_id and str(target_user_id) == str(current_user.id):
                return f(*args, **kwargs)

            flash('Access denied. You can only access your own data.', 'error')
            return redirect(url_for('resident.dashboard'))

        return decorated_function
    return decorator


def ajax_login_required(f):
    """
    Decorator for AJAX routes that returns JSON response
    instead of redirect when user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return {
                'success': False,
                'error': 'Authentication required',
                'redirect_url': url_for('auth.login')
            }, 401

        return f(*args, **kwargs)

    return decorated_function


def ajax_admin_required(f):
    """
    Decorator for AJAX routes that requires admin role.
    Returns JSON response instead of redirect when user lacks privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return {
                'success': False,
                'error': 'Authentication required',
                'redirect_url': url_for('auth.login')
            }, 401

        if not current_user.is_admin():
            return {
                'success': False,
                'error': 'Admin privileges required',
                'redirect_url': url_for('resident.dashboard')
            }, 403

        return f(*args, **kwargs)

    return decorated_function


def role_required(allowed_roles):
    """
    Generic role-based access control decorator.

    Args:
        allowed_roles: List or tuple of allowed roles (e.g., ['admin', 'resident'])

    Usage: @role_required(['admin'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))

            if current_user.role not in allowed_roles:
                flash(f'Access denied. {", ".join(allowed_roles).title()} privileges required.', 'error')
                # Redirect to the first allowed role's dashboard, or login page
                if 'admin' in allowed_roles:
                    return redirect(url_for('admin.dashboard'))
                elif 'resident' in allowed_roles:
                    return redirect(url_for('resident.dashboard'))
                else:
                    return redirect(url_for('auth.login'))

            return f(*args, **kwargs)

        return decorated_function
    return decorator