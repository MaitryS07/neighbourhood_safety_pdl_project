from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.user import User
from models.member import Member
from models import db
from decorators import resident_required, ajax_login_required
import sqlalchemy as sa

# Create blueprint
resident_bp = Blueprint('resident', __name__, url_prefix='/resident')


@resident_bp.route('/dashboard')
@resident_required
def dashboard():
    """Display resident dashboard with safety information and updates"""
    # Get dashboard information
    dashboard_info = get_resident_dashboard_info()

    # Get safety tips
    safety_tips = get_safety_tips()

    # Get emergency contacts
    emergency_contacts = get_emergency_contacts()

    # Get neighborhood updates
    updates = get_neighborhood_updates()

    return render_template('resident/dashboard.html',
                         dashboard_info=dashboard_info,
                         safety_tips=safety_tips,
                         emergency_contacts=emergency_contacts,
                         updates=updates)


@resident_bp.route('/api/safety-alerts')
@ajax_login_required
def api_safety_alerts():
    """Get safety alerts via AJAX"""
    alerts = get_safety_alerts()
    return jsonify({
        'success': True,
        'data': alerts
    })


@resident_bp.route('/api/emergency-contacts')
@ajax_login_required
def api_emergency_contacts():
    """Get emergency contacts via AJAX"""
    contacts = get_emergency_contacts()
    return jsonify({
        'success': True,
        'data': contacts
    })


@resident_bp.route('/api/neighborhood-updates')
@ajax_login_required
def api_neighborhood_updates():
    """Get neighborhood updates via AJAX"""
    limit = request.args.get('limit', 5, type=int)
    updates = get_neighborhood_updates(limit)
    return jsonify({
        'success': True,
        'data': updates
    })


@resident_bp.route('/profile')
@resident_required
def profile():
    """Display resident profile page"""
    user = current_user
    return render_template('resident/profile.html', user=user)


@resident_bp.route('/profile/update', methods=['POST'])
@ajax_login_required
def update_profile():
    """Update resident profile via AJAX"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    try:
        user = current_user

        # Update basic info
        if username and username != user.username:
            if len(username) < 3:
                return jsonify({
                    'success': False,
                    'error': 'Username must be at least 3 characters long'
                }), 400
            if User.username_exists(username):
                return jsonify({
                    'success': False,
                    'error': 'Username already exists'
                }), 400
            user.username = username

        if email and email != user.email:
            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email.lower()):
                return jsonify({
                    'success': False,
                    'error': 'Invalid email format'
                }), 400
            if User.email_exists(email.lower()):
                return jsonify({
                    'success': False,
                    'error': 'Email already exists'
                }), 400
            user.email = email.lower()

        # Update password if provided
        if new_password:
            if not current_password:
                return jsonify({
                    'success': False,
                    'error': 'Current password is required to change password'
                }), 400

            if not user.check_password(current_password):
                return jsonify({
                    'success': False,
                    'error': 'Current password is incorrect'
                }), 400

            if len(new_password) < 6:
                return jsonify({
                    'success': False,
                    'error': 'Password must be at least 6 characters long'
                }), 400

            if new_password != confirm_password:
                return jsonify({
                    'success': False,
                    'error': 'Passwords do not match'
                }), 400

            user.set_password(new_password)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update profile'
        }), 500


@resident_bp.route('/safety-info')
@resident_required
def safety_info():
    """Display detailed safety information page"""
    safety_categories = get_safety_categories()
    return render_template('resident/safety_info.html',
                         safety_categories=safety_categories)


@resident_bp.route('/emergency')
@resident_required
def emergency():
    """Display emergency information page"""
    emergency_contacts = get_emergency_contacts()
    emergency_procedures = get_emergency_procedures()
    return render_template('resident/emergency.html',
                         emergency_contacts=emergency_contacts,
                         emergency_procedures=emergency_procedures)


# Helper functions
def get_resident_dashboard_info():
    """Get resident dashboard information"""
    total_members = Member.query.count()
    recent_members = Member.query.filter(
        Member.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()

    return {
        'user': current_user.to_dict(),
        'member_count': total_members,
        'recent_members': recent_members,
        'last_login': datetime.utcnow().isoformat(),  # Could track actual login times
        'welcome_message': get_welcome_message()
    }


def get_welcome_message():
    """Get personalized welcome message based on time of day"""
    hour = datetime.utcnow().hour
    username = current_user.username

    if 5 <= hour < 12:
        return f"Good morning, {username}!"
    elif 12 <= hour < 17:
        return f"Good afternoon, {username}!"
    elif 17 <= hour < 22:
        return f"Good evening, {username}!"
    else:
        return f"Good night, {username}!"


def get_safety_tips():
    """Get safety tips for residents"""
    return [
        {
            'id': 1,
            'title': 'Keep Doors and Windows Locked',
            'description': 'Always lock your doors and windows, even when you\'re at home.',
            'icon': 'lock',
            'category': 'home_security'
        },
        {
            'id': 2,
            'title': 'Know Your Neighbors',
            'description': 'Build relationships with your neighbors for community safety.',
            'icon': 'users',
            'category': 'community'
        },
        {
            'id': 3,
            'title': 'Emergency Contacts Ready',
            'description': 'Keep emergency contact numbers easily accessible.',
            'icon': 'phone',
            'category': 'emergency'
        },
        {
            'id': 4,
            'title': 'Regular Security Checks',
            'description': 'Check your home security measures regularly.',
            'icon': 'shield',
            'category': 'home_security'
        },
        {
            'id': 5,
            'title': 'Report Suspicious Activity',
            'description': 'Report any suspicious activity to local authorities immediately.',
            'icon': 'alert',
            'category': 'awareness'
        },
        {
            'id': 6,
            'title': 'Well-Lit Areas',
            'description': 'Ensure your property has adequate lighting, especially at entrances.',
            'icon': 'lightbulb',
            'category': 'home_security'
        }
    ]


def get_emergency_contacts():
    """Get emergency contact information"""
    return [
        {
            'id': 1,
            'name': 'Emergency Services',
            'number': '911',
            'description': 'Police, Fire, and Medical emergencies',
            'type': 'emergency',
            'available_24_7': True
        },
        {
            'id': 2,
            'name': 'Local Police Department',
            'number': '(555) 123-4567',
            'description': 'Non-emergency police assistance',
            'type': 'police',
            'available_24_7': True
        },
        {
            'id': 3,
            'name': 'Fire Department',
            'number': '(555) 234-5678',
            'description': 'Fire emergencies and non-emergency inquiries',
            'type': 'fire',
            'available_24_7': True
        },
        {
            'id': 4,
            'name': 'Medical Emergency',
            'number': '(555) 345-6789',
            'description': 'Medical emergencies and hospital information',
            'type': 'medical',
            'available_24_7': True
        },
        {
            'id': 5,
            'name': 'Neighborhood Watch Coordinator',
            'number': '(555) 456-7890',
            'description': 'Neighborhood safety coordination',
            'type': 'community',
            'available_24_7': False
        },
        {
            'id': 6,
            'name': 'Poison Control',
            'number': '1-800-222-1222',
            'description': 'Poison emergencies and information',
            'type': 'medical',
            'available_24_7': True
        }
    ]


def get_neighborhood_updates(limit=5):
    """Get neighborhood updates and announcements"""
    # In a real application, this would come from a database
    # For now, returning sample data
    updates = [
        {
            'id': 1,
            'title': 'Community Meeting Next Tuesday',
            'content': 'Join us for our monthly community safety meeting at the community center.',
            'date': (datetime.utcnow() - timedelta(days=2)).isoformat(),
            'type': 'meeting',
            'priority': 'normal'
        },
        {
            'id': 2,
            'title': 'Street Lighting Update',
            'content': 'New LED street lights will be installed this week on Main Street.',
            'date': (datetime.utcnow() - timedelta(days=5)).isoformat(),
            'type': 'maintenance',
            'priority': 'normal'
        },
        {
            'id': 3,
            'title': 'Neighborhood Watch Program',
            'content': 'We\'re looking for volunteers to join our neighborhood watch program.',
            'date': (datetime.utcnow() - timedelta(days=7)).isoformat(),
            'type': 'program',
            'priority': 'high'
        },
        {
            'id': 4,
            'title': 'Community BBQ This Weekend',
            'content': 'Annual community BBQ this Saturday at the park. All residents welcome!',
            'date': (datetime.utcnow() - timedelta(days=10)).isoformat(),
            'type': 'event',
            'priority': 'normal'
        },
        {
            'id': 5,
            'title': 'Security Camera Installation',
            'content': 'New security cameras have been installed at key neighborhood locations.',
            'date': (datetime.utcnow() - timedelta(days=14)).isoformat(),
            'type': 'security',
            'priority': 'high'
        }
    ]

    return updates[:limit]


def get_safety_alerts():
    """Get current safety alerts"""
    return [
        {
            'id': 1,
            'title': 'Increased Police Presence',
            'message': 'Increased police presence in the area due to recent events.',
            'severity': 'medium',
            'date': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
            'expires': (datetime.utcnow() + timedelta(hours=18)).isoformat()
        },
        {
            'id': 2,
            'title': 'Street Closure',
            'message': 'Main Street will be closed tomorrow from 9 AM to 5 PM for maintenance.',
            'severity': 'low',
            'date': (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            'expires': (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
    ]


def get_safety_categories():
    """Get safety information categories"""
    return [
        {
            'id': 'home_security',
            'name': 'Home Security',
            'description': 'Tips and best practices for securing your home',
            'icon': 'home',
            'tips': [
                'Install deadbolt locks on all exterior doors',
                'Use security cameras or video doorbells',
                'Keep valuables out of sight from windows',
                'Use automatic timers for lights when away'
            ]
        },
        {
            'id': 'personal_safety',
            'name': 'Personal Safety',
            'description': 'Personal safety tips for daily activities',
            'icon': 'user',
            'tips': [
                'Be aware of your surroundings',
                'Walk in well-lit areas at night',
                'Let someone know your travel plans',
                'Carry a personal safety device'
            ]
        },
        {
            'id': 'cyber_security',
            'name': 'Cyber Security',
            'description': 'Protect yourself from online threats',
            'icon': 'laptop',
            'tips': [
                'Use strong, unique passwords',
                'Enable two-factor authentication',
                'Be cautious with public Wi-Fi',
                'Keep software updated'
            ]
        },
        {
            'id': 'emergency_preparedness',
            'name': 'Emergency Preparedness',
            'description': 'Be prepared for emergencies and disasters',
            'icon': 'first-aid',
            'tips': [
                'Create an emergency kit',
                'Have a family emergency plan',
                'Keep important documents safe',
                'Know evacuation routes'
            ]
        }
    ]


def get_emergency_procedures():
    """Get emergency procedures"""
    return [
        {
            'type': 'fire',
            'title': 'Fire Emergency',
            'steps': [
                'Evacuate immediately',
                'Call 911 from a safe location',
                'Do not use elevators',
                'Feel doors before opening - if hot, find another exit',
                'Stay low to avoid smoke inhalation'
            ]
        },
        {
            'type': 'medical',
            'title': 'Medical Emergency',
            'steps': [
                'Call 911 immediately',
                'Stay with the person if possible',
                'Follow operator instructions',
                'Gather any medications the person takes',
                'Unlock the door for emergency responders'
            ]
        },
        {
            'type': 'intruder',
            'title': 'Intruder/Suspicious Activity',
            'steps': [
                'Do not confront the intruder',
                'Lock yourself in a safe room',
                'Call 911 immediately',
                'Stay quiet and hide if necessary',
                'Note description for police if safe to do so'
            ]
        }
    ]