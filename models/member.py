from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()

class Member(db.Model):
    """Member model for neighbourhood member management"""

    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow)

    def __init__(self, name, email, phone=None, address=None,
                 emergency_contact=None, emergency_phone=None):
        """Initialize a new member"""
        self.name = name.strip()
        self.email = email.lower().strip()  # Normalize email
        self.phone = phone.strip() if phone else None
        self.address = address.strip() if address else None
        self.emergency_contact = emergency_contact.strip() if emergency_contact else None
        self.emergency_phone = emergency_phone.strip() if emergency_phone else None

    def validate_email(self):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")

    def validate_phone(self, phone_number):
        """Validate phone number format (basic validation)"""
        if phone_number:
            # Remove common phone number formatting
            cleaned_phone = re.sub(r'[^\d+]', '', phone_number)
            if len(cleaned_phone) < 10:
                raise ValueError("Phone number must be at least 10 digits")
            return cleaned_phone
        return None

    def sanitize_phone_numbers(self):
        """Sanitize and validate phone numbers"""
        if self.phone:
            self.phone = self.validate_phone(self.phone)
        if self.emergency_phone:
            self.emergency_phone = self.validate_phone(self.emergency_phone)

    def validate_data(self):
        """Validate all member data"""
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")

        if not self.email:
            raise ValueError("Email is required")

        self.validate_email()

        # Sanitize and validate phone numbers
        self.sanitize_phone_numbers()

        if self.emergency_contact and len(self.emergency_contact.strip()) < 2:
            raise ValueError("Emergency contact name must be at least 2 characters long")

    def to_dict(self):
        """Convert member object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """String representation of the member"""
        return f'<Member {self.name} ({self.email})>'

    @staticmethod
    def find_by_email(email):
        """Find member by email address"""
        return Member.query.filter_by(email=email.lower()).first()

    @staticmethod
    def find_by_name(name):
        """Find member by name (partial match)"""
        return Member.query.filter(Member.name.ilike(f'%{name}%')).all()

    @staticmethod
    def get_all_members(page=None, per_page=20):
        """Get all members with pagination"""
        if page:
            return Member.query.paginate(
                page=page, per_page=per_page, error_out=False
            )
        return Member.query.all()

    @staticmethod
    def email_exists(email):
        """Check if email already exists"""
        return Member.query.filter_by(email=email.lower()).first() is not None

    @staticmethod
    def create_member(name, email, phone=None, address=None,
                     emergency_contact=None, emergency_phone=None):
        """Create a new member with validation"""
        member = Member(name, email, phone, address,
                       emergency_contact, emergency_phone)
        member.validate_data()

        # Check for duplicate email
        if Member.email_exists(email):
            raise ValueError("A member with this email already exists")

        db.session.add(member)
        return member

    def update_member(self, name=None, email=None, phone=None, address=None,
                     emergency_contact=None, emergency_phone=None):
        """Update member information with validation"""
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValueError("Name must be at least 2 characters long")
            self.name = name

        if email and email != self.email:
            email_lower = email.lower().strip()
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email_lower):
                raise ValueError("Invalid email format")
            # Check for duplicate email
            if Member.email_exists(email_lower):
                raise ValueError("A member with this email already exists")
            self.email = email_lower

        if phone is not None:
            self.phone = self.validate_phone(phone) if phone else None

        if address is not None:
            self.address = address.strip() if address else None

        if emergency_contact is not None:
            emergency_contact = emergency_contact.strip()
            if emergency_contact and len(emergency_contact) < 2:
                raise ValueError("Emergency contact name must be at least 2 characters long")
            self.emergency_contact = emergency_contact

        if emergency_phone is not None:
            self.emergency_phone = self.validate_phone(emergency_phone) if emergency_phone else None

        self.updated_at = datetime.utcnow()

    @staticmethod
    def search_members(query, page=None, per_page=20):
        """Search members by name, email, or phone"""
        search_pattern = f'%{query}%'
        member_query = Member.query.filter(
            (Member.name.ilike(search_pattern)) |
            (Member.email.ilike(search_pattern)) |
            (Member.phone.ilike(search_pattern))
        )

        if page:
            return member_query.paginate(
                page=page, per_page=per_page, error_out=False
            )
        return member_query.all()