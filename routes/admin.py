from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.user import User
from models.member import Member
from models import db
from decorators import admin_required, ajax_admin_required
import sqlalchemy as sa

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Display admin dashboard with statistics and overview"""
    # Get dashboard statistics
    stats = get_dashboard_statistics()

    # Get recent activity
    recent_activity = get_recent_activity()

    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_activity=recent_activity)


@admin_bp.route('/api/stats')
@ajax_admin_required
def api_stats():
    """Get dashboard statistics via AJAX"""
    stats = get_dashboard_statistics()
    return jsonify({
        'success': True,
        'data': stats
    })


@admin_bp.route('/api/recent-activity')
@ajax_admin_required
def api_recent_activity():
    """Get recent activity via AJAX"""
    limit = request.args.get('limit', 10, type=int)
    activity = get_recent_activity(limit)
    return jsonify({
        'success': True,
        'data': activity
    })


@admin_bp.route('/api/member-stats')
@ajax_admin_required
def api_member_stats():
    """Get member statistics for charts"""
    # Member registration trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    member_trends = db.session.query(
        sa.func.date(Member.created_at).label('date'),
        sa.func.count(Member.id).label('count')
    ).filter(
        Member.created_at >= thirty_days_ago
    ).group_by(
        sa.func.date(Member.created_at)
    ).order_by('date').all()

    # User registration trends (last 30 days)
    user_trends = db.session.query(
        sa.func.date(User.created_at).label('date'),
        sa.func.count(User.id).label('count')
    ).filter(
        User.created_at >= thirty_days_ago
    ).group_by(
        sa.func.date(User.created_at)
    ).order_by('date').all()

    return jsonify({
        'success': True,
        'data': {
            'member_trends': [
                {'date': str(trend.date), 'count': trend.count}
                for trend in member_trends
            ],
            'user_trends': [
                {'date': str(trend.date), 'count': trend.count}
                for trend in user_trends
            ]
        }
    })


@admin_bp.route('/api/system-health')
@ajax_admin_required
def api_system_health():
    """Get system health information"""
    try:
        # Test database connection
        db.session.execute(sa.text('SELECT 1'))
        db_status = 'healthy'
        db_error = None
    except Exception as e:
        db_status = 'error'
        db_error = str(e)

    # Get system info
    total_users = User.query.count()
    total_members = Member.query.count()
    recent_logins = 0  # Could be implemented with login tracking

    health_data = {
        'database': {
            'status': db_status,
            'error': db_error,
            'connection_time': 'N/A'  # Could measure actual connection time
        },
        'statistics': {
            'total_users': total_users,
            'total_members': total_members,
            'recent_logins': recent_logins,
            'system_uptime': 'N/A'  # Could track actual uptime
        },
        'timestamp': datetime.utcnow().isoformat()
    }

    return jsonify({
        'success': True,
        'data': health_data
    })


# Helper functions
def get_dashboard_statistics():
    """Get dashboard statistics"""
    # User statistics
    total_users = User.query.count()
    admin_users = User.query.filter_by(role='admin').count()
    resident_users = User.query.filter_by(role='resident').count()

    # Member statistics
    total_members = Member.query.count()
    recent_members = Member.query.filter(
        Member.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()

    # System statistics
    recent_logins = 0  # Could be implemented with login tracking table
    active_sessions = 0  # Could be implemented with session tracking

    return {
        'users': {
            'total': total_users,
            'admins': admin_users,
            'residents': resident_users,
            'recent_registrations': User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
        },
        'members': {
            'total': total_members,
            'recent_additions': recent_members
        },
        'system': {
            'recent_logins': recent_logins,
            'active_sessions': active_sessions,
            'server_time': datetime.utcnow().isoformat()
        }
    }


def get_recent_activity(limit=10):
    """Get recent activity for dashboard"""
    activities = []

    # Recent user registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(limit//2).all()
    for user in recent_users:
        activities.append({
            'type': 'user_registration',
            'message': f'New {user.get_role_display()} registered: {user.username}',
            'timestamp': user.created_at.isoformat(),
            'details': {
                'user_id': user.id,
                'email': user.email,
                'role': user.role
            }
        })

    # Recent member additions
    recent_members = Member.query.order_by(Member.created_at.desc()).limit(limit//2).all()
    for member in recent_members:
        activities.append({
            'type': 'member_addition',
            'message': f'New member added: {member.name}',
            'timestamp': member.created_at.isoformat(),
            'details': {
                'member_id': member.id,
                'email': member.email
            }
        })

    # Sort by timestamp (most recent first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)

    return activities[:limit]


@admin_bp.route('/users')
@admin_required
def users():
    """Display user management page"""
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', '')
    search = request.args.get('search', '')

    # Build query
    query = User.query

    if role:
        query = query.filter_by(role=role)

    if search:
        query = query.filter(
            sa.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    # Paginate
    users_pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('admin/users.html',
                         users_pagination=users_pagination,
                         current_role=role,
                         current_search=search)


@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@ajax_admin_required
def toggle_user_role(user_id):
    """Toggle user role between admin and resident"""
    if user_id == current_user.id:
        return jsonify({
            'success': False,
            'error': 'Cannot change your own role'
        }), 400

    user = User.query.get_or_404(user_id)

    try:
        # Toggle role
        new_role = 'resident' if user.role == 'admin' else 'admin'
        user.role = new_role
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'User role changed to {new_role}',
            'new_role': new_role,
            'new_role_display': user.get_role_display()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update user role'
        }), 500


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@ajax_admin_required
def delete_user(user_id):
    """Delete a user account"""
    if user_id == current_user.id:
        return jsonify({
            'success': False,
            'error': 'Cannot delete your own account'
        }), 400

    user = User.query.get_or_404(user_id)

    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'User {username} has been deleted'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete user'
        }), 500