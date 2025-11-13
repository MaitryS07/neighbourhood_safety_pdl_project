from flask import session, g, current_app
from flask_login import current_user
from datetime import datetime, timedelta


def init_auth_middleware(app):
    """
    Initialize authentication middleware for the Flask application.

    This middleware handles:
    - Session timeout management
    - User context setup
    - Security headers
    - Activity tracking
    """

    @app.before_request
    def before_request():
        """
        Before request handler that sets up user context
        and handles session timeout.
        """
        # Set current user in global context
        g.current_user = current_user

        # Handle session timeout for authenticated users
        if current_user.is_authenticated:
            # Check if session has expired
            session_timeout = current_app.config.get('PERMANENT_SESSION_LIFETIME', 86400)  # 24 hours default
            last_activity = session.get('last_activity')

            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                if datetime.utcnow() - last_activity_time > timedelta(seconds=session_timeout):
                    # Session expired, log out user
                    from flask_login import logout_user
                    logout_user()
                    session.clear()
                    return None  # Let the request continue, user will be redirected to login

            # Update last activity time
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = True

    @app.after_request
    def after_request(response):
        """
        After request handler that adds security headers.
        """
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Only add HSTS in production
        if not current_app.config.get('DEBUG', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy (basic version)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp

        return response

    @app.context_processor
    def inject_user_context():
        """
        Inject user context into templates.
        """
        return {
            'current_user': current_user,
            'is_authenticated': current_user.is_authenticated,
            'is_admin': current_user.is_admin() if current_user.is_authenticated else False,
            'is_resident': current_user.is_resident() if current_user.is_authenticated else False,
        }


class SessionManager:
    """
    Utility class for managing user sessions.
    """

    @staticmethod
    def create_user_session(user, remember=False):
        """
        Create a new user session.

        Args:
            user: The user object
            remember: Whether to remember the user across sessions
        """
        from flask_login import login_user

        # Set session data
        session['last_activity'] = datetime.utcnow().isoformat()
        session.permanent = remember

        # Log in the user
        login_user(user, remember=remember)

        # Store user preferences in session
        session['user_preferences'] = {
            'theme': user.role,  # Could be extended with actual preferences
            'language': 'en'
        }

    @staticmethod
    def destroy_user_session():
        """
        Destroy the current user session.
        """
        from flask_login import logout_user

        # Clear session data
        session.clear()

        # Log out the user
        logout_user()

    @staticmethod
    def is_session_valid():
        """
        Check if the current session is valid.

        Returns:
            bool: True if session is valid, False otherwise
        """
        if not current_user.is_authenticated:
            return False

        last_activity = session.get('last_activity')
        if not last_activity:
            return False

        try:
            last_activity_time = datetime.fromisoformat(last_activity)
            session_timeout = current_app.config.get('PERMANENT_SESSION_LIFETIME', 86400)

            return datetime.utcnow() - last_activity_time <= timedelta(seconds=session_timeout)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def extend_session():
        """
        Extend the current session timeout.
        """
        if current_user.is_authenticated:
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = True

    @staticmethod
    def get_session_info():
        """
        Get information about the current session.

        Returns:
            dict: Session information
        """
        if not current_user.is_authenticated:
            return {'valid': False}

        last_activity = session.get('last_activity')
        if last_activity:
            try:
                last_activity_time = datetime.fromisoformat(last_activity)
                session_timeout = current_app.config.get('PERMANENT_SESSION_LIFETIME', 86400)
                time_remaining = session_timeout - (datetime.utcnow() - last_activity_time).total_seconds()

                return {
                    'valid': True,
                    'last_activity': last_activity_time.isoformat(),
                    'time_remaining_seconds': max(0, time_remaining),
                    'user_id': current_user.id,
                    'user_role': current_user.role
                }
            except (ValueError, TypeError):
                pass

        return {'valid': True, 'user_id': current_user.id, 'user_role': current_user.role}