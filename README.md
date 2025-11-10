# Neighbourhood Safety Web Application

A comprehensive web application for neighbourhood safety management with role-based access control, member management, and safety information sharing.

## Features

### 🔐 Authentication & Security
- User registration with role selection (Admin/Resident)
- Secure login/logout with session management
- Password hashing with Werkzeug
- CSRF protection
- Session timeout handling

### 👥 Role-Based Access Control
- **Admin**: Full access to member management, user administration, and system statistics
- **Resident**: Access to safety information, emergency contacts, and personal profile

### 📊 Member Management
- Add, edit, and delete neighbourhood members
- Contact information management
- Emergency contact tracking
- Search and filter functionality
- CSV export capabilities

### 🏠 Resident Features
- Personalized dashboard with safety tips
- Emergency contact information
- Neighborhood updates and announcements
- Profile management

### 📱 Responsive Design
- Mobile-friendly interface
- Modern UI with smooth animations
- Accessible design patterns

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Authentication**: Flask-Login
- **Security**: Flask-WTF, Werkzeug
- **Icons**: Font Awesome

## Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 5.7+ or 8.0+
- pip package manager

### 1. Clone the Repository
```bash
git clone <repository-url>
cd neighbourhood_safety_pdl_project
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Create MySQL Database
```sql
CREATE DATABASE neighbourhood_safety;
CREATE USER 'neighbourhood_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON neighbourhood_safety.* TO 'neighbourhood_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Run Database Schema
```bash
mysql -u neighbourhood_user -p neighbourhood_safety < database/schema.sql
```

### 5. Environment Configuration
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=neighbourhood_user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=neighbourhood_safety
```

### 6. Initialize Database
```bash
flask init-db
```

### 7. Create Admin User (Optional)
```bash
flask create-admin
```

### 8. Seed Sample Data (Optional)
```bash
flask seed-data
```

### 9. Run the Application
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Default Users

After running `seed-data`, you can use these default accounts:

### Admin User
- **Email**: admin@example.com
- **Password**: admin123
- **Role**: Administrator

### Resident User
- **Email**: resident1@example.com
- **Password**: resident123
- **Role**: Resident

## Project Structure

```
neighbourhood_safety_pdl_project/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── database/
│   └── schema.sql                 # Database creation script
├── models/
│   ├── __init__.py
│   ├── user.py                    # User model
│   └── member.py                  # Member model
├── routes/
│   ├── __init__.py
│   ├── auth.py                    # Authentication routes
│   ├── admin.py                   # Admin dashboard routes
│   ├── resident.py                # Resident dashboard routes
│   └── members.py                 # Member management routes
├── middleware/
│   └── auth.py                    # Authentication middleware
├── decorators/
│   └── access_control.py          # Role-based decorators
├── templates/
│   ├── base.html                  # Base template
│   ├── auth/
│   │   ├── login.html             # Login page
│   │   └── signup.html            # Registration page
│   ├── admin/
│   │   └── dashboard.html         # Admin dashboard
│   ├── resident/
│   │   └── dashboard.html         # Resident dashboard
│   ├── members.html               # Member management
│   └── errors/                    # Error pages
├── static/
│   ├── css/
│   │   └── style.css              # Main stylesheet
│   └── js/
│       └── main.js                # Frontend functionality
└── README.md                      # This file
```

## Available CLI Commands

```bash
# Initialize database tables
flask init-db

# Create admin user
flask create-admin

# Reset database (WARNING: Deletes all data)
flask reset-db

# Seed sample data
flask seed-data

# Run development server
flask run

# Run in production mode
export FLASK_ENV=production
flask run
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/signup` - User registration
- `POST /auth/logout` - User logout

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `POST /admin/users/<id>/toggle-role` - Toggle user role
- `POST /admin/users/<id>/delete` - Delete user

### Member Management
- `GET /members` - List members (Admin only)
- `POST /members/add` - Add new member (Admin only)
- `POST /members/<id>/update` - Update member (Admin only)
- `POST /members/<id>/delete` - Delete member (Admin only)
- `GET /members/export` - Export members as CSV (Admin only)

### Resident Routes
- `GET /resident/dashboard` - Resident dashboard
- `GET /resident/profile` - User profile
- `POST /resident/profile/update` - Update profile

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest

# Run tests
pytest
```

### Code Style
This project follows PEP 8 Python style guidelines. Use the following tools to maintain code quality:

```bash
# Install development tools
pip install flake8 black

# Check code style
flake8 .

# Format code
black .
```

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- CSRF protection on all forms
- SQL injection prevention with SQLAlchemy
- XSS protection with Jinja2 templating
- Secure session configuration
- Input validation and sanitization

## Deployment

### Production Setup

1. **Environment Configuration**:
   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=your-secure-secret-key
   ```

2. **Database**: Use a production MySQL instance with proper security settings

3. **Web Server**: Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

4. **Reverse Proxy**: Configure Nginx or Apache as a reverse proxy

### Docker Deployment

A Docker configuration can be added for containerized deployment.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team.

## Roadmap

- [ ] Email notifications for system events
- [ ] Advanced member analytics and reporting
- [ ] Mobile application
- [ ] Integration with emergency services
- [ ] Multi-language support
- [ ] Advanced security features (2FA, etc.)