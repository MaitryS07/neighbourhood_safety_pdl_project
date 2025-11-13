from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from models.user import User
from models.member import Member
from models import db
from decorators import logout_required, login_required
from middleware.auth import SessionManager
import re

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    """Handle user login"""
    if request.method == 'POST':
        # Handle AJAX requests
        if request.is_json:
            return handle_ajax_login()

        # Handle form submissions
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        # Validation
        errors = validate_login_form(email, password)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/login.html', email=email, remember=remember)

        # Authenticate user
        user = authenticate_user(email, password)
        if user:
            # Create session
            SessionManager.create_user_session(user, remember)
            flash(f'Welcome back, {user.username}!', 'success')

            # Redirect to intended URL or appropriate dashboard
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            return redirect(
                url_for('admin.dashboard') if user.is_admin()
                else url_for('resident.dashboard')
            )
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
@logout_required
def signup():
    """Handle user registration"""
    if request.method == 'POST':
        # Handle AJAX requests
        if request.is_json:
            return handle_ajax_signup()

        # Handle form submissions
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'resident')

        # Validation
        errors = validate_signup_form(username, email, password, confirm_password, role)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/signup.html',
                                 username=username, email=email, role=role)

        # Create user
        try:
            user = User.create_user(username, email, password, role)
            db.session.commit()

            # Auto-login after signup
            SessionManager.create_user_session(user, remember=True)
            flash(f'Account created successfully! Welcome, {user.username}!', 'success')

            # Redirect based on role
            return redirect(
                url_for('admin.dashboard') if user.is_admin()
                else url_for('resident.dashboard')
            )

        except ValueError as e:
            flash(str(e), 'error')
            return render_template('auth/signup.html',
                                 username=username, email=email, role=role)
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.', 'error')
            current_app.logger.error(f"User creation error: {str(e)}")

    return render_template('auth/signup.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout"""
    # Handle AJAX requests
    if request.is_json:
        SessionManager.destroy_user_session()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect_url': url_for('auth.login')
        })

    # Handle form submissions
    username = current_user.username
    SessionManager.destroy_user_session()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/check-session')
def check_session():
    """Check if user session is valid (for AJAX requests)"""
    session_info = SessionManager.get_session_info()
    return jsonify(session_info)


@auth_bp.route('/extend-session')
@login_required
def extend_session():
    """Extend user session timeout (for AJAX requests)"""
    SessionManager.extend_session()
    session_info = SessionManager.get_session_info()
    return jsonify(session_info)


# Helper functions
def validate_login_form(email, password):
    """Validate login form data"""
    errors = []

    if not email:
        errors.append('Email is required')
    elif not is_valid_email(email):
        errors.append('Please enter a valid email address')

    if not password:
        errors.append('Password is required')

    return errors


def validate_signup_form(username, email, password, confirm_password, role):
    """Validate signup form data"""
    errors = []

    # Username validation
    if not username:
        errors.append('Username is required')
    elif len(username) < 3:
        errors.append('Username must be at least 3 characters long')
    elif len(username) > 50:
        errors.append('Username must be less than 50 characters')
    elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
        errors.append('Username can only contain letters, numbers, underscores, and hyphens')

    # Email validation
    if not email:
        errors.append('Email is required')
    elif not is_valid_email(email):
        errors.append('Please enter a valid email address')

    # Password validation
    if not password:
        errors.append('Password is required')
    elif len(password) < 6:
        errors.append('Password must be at least 6 characters long')
    elif len(password) > 128:
        errors.append('Password must be less than 128 characters')

    # Password confirmation
    if password != confirm_password:
        errors.append('Passwords do not match')

    # Role validation
    if role not in ['admin', 'resident']:
        errors.append('Invalid role selected')

    return errors


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_safe_url(target):
    """Check if URL is safe for redirect"""
    from urllib.parse import urlparse

    if not target:
        return False

    target_url = urlparse(target)
    current_url = urlparse(request.host_url)

    return (
        target_url.scheme == current_url.scheme and
        target_url.netloc == current_url.netloc
    )


def authenticate_user(email, password):
    """Authenticate user with email and password"""
    if not email or not password:
        return None

    # Find user by email (case insensitive)
    user = User.find_by_email(email)
    if user and user.check_password(password):
        return user

    return None


def handle_ajax_login():
    """Handle AJAX login requests"""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)

    # Validation
    errors = validate_login_form(email, password)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400

    # Authentication
    user = authenticate_user(email, password)
    if user:
        SessionManager.create_user_session(user, remember)

        # Determine redirect URL
        next_page = data.get('next')
        if next_page and is_safe_url(next_page):
            redirect_url = next_page
        else:
            redirect_url = url_for('admin.dashboard') if user.is_admin() else url_for('resident.dashboard')

        return jsonify({
            'success': True,
            'message': f'Welcome back, {user.username}!',
            'redirect_url': redirect_url,
            'user': user.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'errors': ['Invalid email or password']
        }), 401


def handle_ajax_signup():
    """Handle AJAX signup requests"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    role = data.get('role', 'resident')

    # Validation
    errors = validate_signup_form(username, email, password, confirm_password, role)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400

    # Create user
    try:
        user = User.create_user(username, email, password, role)
        db.session.commit()

        # Auto-login after signup
        SessionManager.create_user_session(user, remember=True)

        # Determine redirect URL
        redirect_url = url_for('admin.dashboard') if user.is_admin() else url_for('resident.dashboard')

        return jsonify({
            'success': True,
            'message': f'Account created successfully! Welcome, {user.username}!',
            'redirect_url': redirect_url,
            'user': user.to_dict()
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'errors': [str(e)]
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User creation error: {str(e)}")
        return jsonify({
            'success': False,
            'errors': ['An error occurred while creating your account. Please try again.']
        }), 500