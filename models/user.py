from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'resident', name='user_role'),
                     nullable=False, default='resident')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow)

    # Relationship with members (if user manages specific members)
    # members = db.relationship('Member', backref='manager', lazy=True)

    def __init__(self, username, email, password, role='resident'):
        """Initialize a new user"""
        self.username = username
        self.email = email.lower()  # Normalize email to lowercase
        self.role = role
        self.set_password(password)

    def set_password(self, password):
        """Hash and set the user's password"""
        if not password:
            raise ValueError("Password cannot be empty")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'

    def is_resident(self):
        """Check if user has resident role"""
        return self.role == 'resident'

    def get_role_display(self):
        """Get user-friendly role name"""
        return 'Admin' if self.is_admin() else 'Resident'

    def to_dict(self):
        """Convert user object to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'role_display': self.get_role_display(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """String representation of the user"""
        return f'<User {self.username} ({self.email})>'

    @staticmethod
    def find_by_email(email):
        """Find user by email address"""
        return User.query.filter_by(email=email.lower()).first()

    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def email_exists(email):
        """Check if email already exists"""
        return User.query.filter_by(email=email.lower()).first() is not None

    @staticmethod
    def username_exists(username):
        """Check if username already exists"""
        return User.query.filter_by(username=username).first() is not None

    @staticmethod
    def create_user(username, email, password, role='resident'):
        """Create a new user with validation"""
        # Validate inputs
        if not username or not email or not password:
            raise ValueError("All fields are required")

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

        if role not in ['admin', 'resident']:
            raise ValueError("Invalid role. Must be 'admin' or 'resident'")

        # Check for duplicates
        if User.email_exists(email):
            raise ValueError("Email already exists")

        if User.username_exists(username):
            raise ValueError("Username already exists")

        # Create and return new user
        user = User(username, email, password, role)
        db.session.add(user)
        return user

    def update_profile(self, username=None, email=None):
        """Update user profile with validation"""
        if username and username != self.username:
            if len(username) < 3:
                raise ValueError("Username must be at least 3 characters long")
            if User.username_exists(username):
                raise ValueError("Username already exists")
            self.username = username

        if email and email != self.email:
            email_lower = email.lower()
            if User.email_exists(email_lower):
                raise ValueError("Email already exists")
            self.email = email_lower

        self.updated_at = datetime.utcnow()