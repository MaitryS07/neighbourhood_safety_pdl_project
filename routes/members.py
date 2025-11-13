from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from models.member import Member
from models import db
from decorators import admin_required, ajax_admin_required
import sqlalchemy as sa

# Create blueprint
members_bp = Blueprint('members', __name__)


@members_bp.route('/')
@admin_required
def list_members():
    """Display members list page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'name')
    sort_order = request.args.get('order', 'asc')

    # Build query
    query = Member.query

    # Apply search filter
    if search:
        query = Member.search_members(search)

    # Apply sorting
    if sort_by == 'name':
        if sort_order == 'desc':
            query = query.order_by(Member.name.desc())
        else:
            query = query.order_by(Member.name.asc())
    elif sort_by == 'email':
        if sort_order == 'desc':
            query = query.order_by(Member.email.desc())
        else:
            query = query.order_by(Member.email.asc())
    elif sort_by == 'created_at':
        if sort_order == 'desc':
            query = query.order_by(Member.created_at.desc())
        else:
            query = query.order_by(Member.created_at.asc())

    # Paginate
    members_pagination = query.paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('members.html',
                         members_pagination=members_pagination,
                         current_search=search,
                         current_sort=sort_by,
                         current_sort_order=sort_order)


@members_bp.route('/add', methods=['POST'])
@ajax_admin_required
def add_member():
    """Add a new member via AJAX"""
    data = request.get_json()

    # Extract and validate form data
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    emergency_contact = data.get('emergency_contact', '').strip()
    emergency_phone = data.get('emergency_phone', '').strip()

    # Validation
    errors = validate_member_form(name, email, phone, address, emergency_contact, emergency_phone)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400

    try:
        # Create new member
        member = Member.create_member(
            name=name,
            email=email,
            phone=phone if phone else None,
            address=address if address else None,
            emergency_contact=emergency_contact if emergency_contact else None,
            emergency_phone=emergency_phone if emergency_phone else None
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Member {member.name} has been added successfully!',
            'member': member.to_dict()
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'errors': [str(e)]
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'errors': ['An error occurred while adding the member. Please try again.']
        }), 500


@members_bp.route('/<int:member_id>')
@admin_required
def get_member(member_id):
    """Get member details via AJAX"""
    member = Member.query.get_or_404(member_id)

    return jsonify({
        'success': True,
        'member': member.to_dict()
    })


@members_bp.route('/<int:member_id>/update', methods=['POST'])
@ajax_admin_required
def update_member(member_id):
    """Update member information via AJAX"""
    member = Member.query.get_or_404(member_id)
    data = request.get_json()

    # Extract form data
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    emergency_contact = data.get('emergency_contact', '').strip()
    emergency_phone = data.get('emergency_phone', '').strip()

    # Validation
    errors = validate_member_form(name, email, phone, address, emergency_contact, emergency_phone, member_id)
    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400

    try:
        # Update member
        member.update_member(
            name=name,
            email=email,
            phone=phone if phone else None,
            address=address if address else None,
            emergency_contact=emergency_contact if emergency_contact else None,
            emergency_phone=emergency_phone if emergency_phone else None
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Member {member.name} has been updated successfully!',
            'member': member.to_dict()
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'errors': [str(e)]
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'errors': ['An error occurred while updating the member. Please try again.']
        }), 500


@members_bp.route('/<int:member_id>/delete', methods=['POST'])
@ajax_admin_required
def delete_member(member_id):
    """Delete a member via AJAX"""
    member = Member.query.get_or_404(member_id)

    try:
        name = member.name
        db.session.delete(member)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Member {name} has been deleted successfully!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'errors': ['An error occurred while deleting the member. Please try again.']
        }), 500


@members_bp.route('/search')
@ajax_admin_required
def search_members():
    """Search members via AJAX"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    if not query:
        return jsonify({
            'success': False,
            'errors': ['Search query is required']
        }), 400

    try:
        members_pagination = Member.search_members(query, page=page)
        members = [member.to_dict() for member in members_pagination.items]

        return jsonify({
            'success': True,
            'members': members,
            'pagination': {
                'page': members_pagination.page,
                'pages': members_pagination.pages,
                'per_page': members_pagination.per_page,
                'total': members_pagination.total,
                'has_prev': members_pagination.has_prev,
                'has_next': members_pagination.has_next,
                'prev_num': members_pagination.prev_num,
                'next_num': members_pagination.next_num
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'errors': ['An error occurred while searching members. Please try again.']
        }), 500


@members_bp.route('/export')
@admin_required
def export_members():
    """Export members data as CSV"""
    import csv
    from io import StringIO
    from flask import Response

    try:
        # Get all members
        members = Member.query.all()

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Name', 'Email', 'Phone', 'Address',
            'Emergency Contact', 'Emergency Phone', 'Created At', 'Updated At'
        ])

        # Write member data
        for member in members:
            writer.writerow([
                member.id,
                member.name,
                member.email,
                member.phone or '',
                member.address or '',
                member.emergency_contact or '',
                member.emergency_phone or '',
                member.created_at.strftime('%Y-%m-%d %H:%M:%S') if member.created_at else '',
                member.updated_at.strftime('%Y-%m-%d %H:%M:%S') if member.updated_at else ''
            ])

        # Create response
        output.seek(0)
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=members_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )

        return response

    except Exception as e:
        flash('An error occurred while exporting members data.', 'error')
        return redirect(url_for('members.list_members'))


@members_bp.route('/stats')
@ajax_admin_required
def get_member_stats():
    """Get member statistics via AJAX"""
    try:
        total_members = Member.query.count()
        recent_members = Member.query.filter(
            Member.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()

        members_with_phone = Member.query.filter(Member.phone.isnot(None)).count()
        members_with_emergency = Member.query.filter(
            Member.emergency_contact.isnot(None)
        ).count()

        # Monthly registration trends (last 6 months)
        from sqlalchemy import func, extract
        monthly_trends = db.session.query(
            extract('year', Member.created_at).label('year'),
            extract('month', Member.created_at).label('month'),
            func.count(Member.id).label('count')
        ).filter(
            Member.created_at >= datetime.utcnow() - timedelta(days=180)
        ).group_by(
            extract('year', Member.created_at),
            extract('month', Member.created_at)
        ).order_by('year', 'month').all()

        return jsonify({
            'success': True,
            'stats': {
                'total_members': total_members,
                'recent_members': recent_members,
                'members_with_phone': members_with_phone,
                'members_with_emergency': members_with_emergency,
                'monthly_trends': [
                    {
                        'year': trend.year,
                        'month': trend.month,
                        'count': trend.count
                    }
                    for trend in monthly_trends
                ]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'errors': ['An error occurred while fetching member statistics.']
        }), 500


# Helper functions
def validate_member_form(name, email, phone, address, emergency_contact, emergency_phone, member_id=None):
    """Validate member form data"""
    errors = []

    # Name validation
    if not name:
        errors.append('Name is required')
    elif len(name) < 2:
        errors.append('Name must be at least 2 characters long')
    elif len(name) > 100:
        errors.append('Name must be less than 100 characters')

    # Email validation
    if not email:
        errors.append('Email is required')
    else:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.lower()):
            errors.append('Please enter a valid email address')
        elif Member.email_exists(email) and (not member_id or Member.query.get(member_id).email != email):
            errors.append('A member with this email already exists')

    # Phone validation (optional)
    if phone:
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        if len(cleaned_phone) < 10:
            errors.append('Phone number must be at least 10 digits')

    # Address validation (optional)
    if address and len(address) > 1000:
        errors.append('Address must be less than 1000 characters')

    # Emergency contact validation (optional)
    if emergency_contact and len(emergency_contact) < 2:
        errors.append('Emergency contact name must be at least 2 characters long')
    elif emergency_contact and len(emergency_contact) > 100:
        errors.append('Emergency contact name must be less than 100 characters')

    # Emergency phone validation (optional)
    if emergency_phone:
        cleaned_phone = re.sub(r'[^\d+]', '', emergency_phone)
        if len(cleaned_phone) < 10:
            errors.append('Emergency phone number must be at least 10 digits')

    return errors