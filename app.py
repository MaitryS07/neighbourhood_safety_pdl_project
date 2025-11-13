from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import config
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register template context processors
    register_context_processors(app)

    # Register CLI commands
    register_cli_commands(app)

    # Initialize authentication middleware
    from middleware.auth import init_auth_middleware
    init_auth_middleware(app)

    return app


def init_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = 'Please re-login to continue.'
    login_manager.needs_refresh_message_category = 'info'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # Request user loader for Flask-Login
    @login_manager.request_loader
    def load_user_from_request(request):
        # This can be extended for API token authentication
        return None


def register_blueprints(app):
    """Register application blueprints"""
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.resident import resident_bp
    from routes.members import members_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(resident_bp)
    app.register_blueprint(members_bp)

    # Register main routes
    register_main_routes(app)


def register_main_routes(app):
    """Register main application routes"""

    @app.route('/')
    def index():
        """Main landing page - redirect to appropriate dashboard or login"""
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('resident.dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return {'status': 'healthy', 'message': 'Neighbourhood Safety Application'}, 200

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': 'Page not found'}, 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        db.session.rollback()
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': 'Internal server error'}, 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': 'Access forbidden'}, 403
        return render_template('errors/403.html'), 403

    @app.context_processor
    def inject_debug_info():
        """Inject debug information in development"""
        if app.debug:
            return {
                'debug': True,
                'config_vars': dict(app.config)
            }
        return {'debug': False}


def register_error_handlers(app):
    """Register custom error handlers"""
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 errors"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': 'Bad request'}, 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle 401 errors"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': 'Unauthorized'}, 401
        return render_template('errors/401.html'), 401


def register_context_processors(app):
    """Register template context processors"""
    @app.context_processor
    def utility_functions():
        """Utility functions for templates"""
        def format_datetime(value, format='%Y-%m-%d %H:%M'):
            """Format datetime for display"""
            if value is None:
                return ''
            return value.strftime(format)

        def format_date(value, format='%Y-%m-%d'):
            """Format date for display"""
            if value is None:
                return ''
            return value.strftime(format)

        def get_url_param(param, default=''):
            """Get URL parameter value"""
            return request.args.get(param, default)

        def is_active_page(endpoint):
            """Check if current page matches endpoint"""
            return request.endpoint == endpoint

        def is_active_menu(*endpoints):
            """Check if current page is in menu endpoints"""
            return request.endpoint in endpoints

        return {
            'format_datetime': format_datetime,
            'format_date': format_date,
            'get_url_param': get_url_param,
            'is_active_page': is_active_page,
            'is_active_menu': is_active_menu,
        }

    @app.context_processor
    def inject_navigation():
        """Inject navigation data"""
        nav_items = {
            'auth': [
                {'name': 'Login', 'endpoint': 'auth.login', 'icon': 'sign-in-alt'},
                {'name': 'Sign Up', 'endpoint': 'auth.signup', 'icon': 'user-plus'}
            ],
            'admin': [
                {'name': 'Dashboard', 'endpoint': 'admin.dashboard', 'icon': 'dashboard'},
                {'name': 'Members', 'endpoint': 'members.list_members', 'icon': 'users'},
                {'name': 'Users', 'endpoint': 'admin.users', 'icon': 'user-shield'},
                {'name': 'Profile', 'endpoint': 'resident.profile', 'icon': 'user'},
            ],
            'resident': [
                {'name': 'Dashboard', 'endpoint': 'resident.dashboard', 'icon': 'dashboard'},
                {'name': 'Safety Info', 'endpoint': 'resident.safety_info', 'icon': 'shield-alt'},
                {'name': 'Emergency', 'endpoint': 'resident.emergency', 'icon': 'phone-alt'},
                {'name': 'Profile', 'endpoint': 'resident.profile', 'icon': 'user'},
            ]
        }

        return {'nav_items': nav_items}


def register_cli_commands(app):
    """Register CLI commands"""
    @app.cli.command()
    def init_db():
        """Initialize the database"""
        from models import user, member

        # Create all tables
        db.create_all()
        print('Database initialized successfully!')

    @app.cli.command()
    def create_admin():
        """Create an admin user"""
        from models.user import User

        email = input('Enter admin email: ')
        username = input('Enter admin username: ')
        password = input('Enter admin password: ')

        try:
            admin_user = User.create_user(username, email, password, 'admin')
            db.session.add(admin_user)
            db.session.commit()
            print(f'Admin user {username} created successfully!')
        except ValueError as e:
            print(f'Error creating admin user: {e}')
        except Exception as e:
            db.session.rollback()
            print(f'Database error: {e}')

    @app.cli.command()
    def reset_db():
        """Reset the database (drop and recreate all tables)"""
        if input('This will delete all data. Are you sure? (y/N): ').lower() == 'y':
            db.drop_all()
            db.create_all()
            print('Database reset successfully!')

    @app.cli.command()
    def seed_data():
        """Seed the database with sample data"""
        from models.user import User
        from models.member import Member

        try:
            # Create sample admin
            admin = User.create_user('admin', 'admin@example.com', 'admin123', 'admin')
            db.session.add(admin)

            # Create sample resident
            resident = User.create_user('resident1', 'resident1@example.com', 'resident123', 'resident')
            db.session.add(resident)

            # Create sample members
            sample_members = [
                {
                    'name': 'John Smith',
                    'email': 'john.smith@example.com',
                    'phone': '+1-555-0101',
                    'address': '123 Main St, Anytown, USA',
                    'emergency_contact': 'Jane Smith',
                    'emergency_phone': '+1-555-0102'
                },
                {
                    'name': 'Alice Johnson',
                    'email': 'alice.johnson@example.com',
                    'phone': '+1-555-0103',
                    'address': '456 Oak Ave, Anytown, USA',
                    'emergency_contact': 'Bob Johnson',
                    'emergency_phone': '+1-555-0104'
                },
                {
                    'name': 'Charlie Brown',
                    'email': 'charlie.brown@example.com',
                    'phone': '+1-555-0105',
                    'address': '789 Pine Rd, Anytown, USA',
                    'emergency_contact': 'Diana Brown',
                    'emergency_phone': '+1-555-0106'
                }
            ]

            for member_data in sample_members:
                member = Member.create_member(**member_data)
                db.session.add(member)

            db.session.commit()
            print('Sample data seeded successfully!')

        except Exception as e:
            db.session.rollback()
            print(f'Error seeding data: {e}')

    @app.cli.command()
    def run_migrations():
        """Run database migrations (placeholder for future migration system)"""
        print('Migration system not yet implemented. Use init-db or reset-db instead.')


# Create application instance
app = create_app()

if __name__ == '__main__':
    # For development only
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )