# BarSan Flask Backend

A Flask-based REST API for the BarSan table reservation system using SQLAlchemy and SQLite with WAL mode for optimal performance.

## 🚀 Features

- **Unified Authentication**: Single login endpoint for both users and admins
- **SQLite WAL Mode**: Write-Ahead Logging for concurrent access without blocking
- **JWT Authentication**: Secure token-based authentication
- **Reservation System**: Complete table reservation management
- **Admin Dashboard**: Administrative interface for managing reservations
- **CORS Support**: Cross-origin resource sharing for frontend integration
- **Docker Ready**: Containerized deployment support
- **Auto Database Setup**: Automatic database creation and seeding

## 🛠️ Tech Stack

- **Framework**: Flask (Python)
- **Database**: SQLite with WAL mode
- **ORM**: SQLAlchemy
- **Authentication**: Flask-JWT-Extended
- **CORS**: Flask-CORS
- **Password Hashing**: Werkzeug
- **Environment**: python-dotenv

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## 🔧 Quick Start

### 1. Setup Environment

\`\`\`bash
# Clone the repository
git clone <repository-url>
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
\`\`\`

### 2. Configure Environment

\`\`\`bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# At minimum, change SECRET_KEY and JWT_SECRET_KEY
\`\`\`

### 3. Run the Application

\`\`\`bash
# Start the development server
python run.py
\`\`\`

The API will be available at `http://localhost:5000`

## 🌐 API Endpoints

### Authentication (Unified)
- `POST /auth/login` - Login for both users and admins
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user/admin info
- `POST /auth/logout` - Logout (clears auth cookie)

### Reservations
- `POST /reservations/temp` - Create temporary reservation (15-min hold)
- `POST /reservations` - Create confirmed reservation
- `GET /reservations/my` - Get user's reservations (requires auth)
- `GET /reservations/<number>` - Get reservation details
- `DELETE /reservations/<number>` - Cancel reservation

### Cafes
- `GET /cafes` - Get all active cafes
- `GET /cafes/<id>` - Get cafe details
- `GET /cafes/<id>/availability` - Get available time slots
- `GET /cafes/<id>/zones/<zone_id>/tables` - Get tables in zone

### Admin (requires admin auth)
- `GET /admin/dashboard/<cafe_id>` - Get dashboard statistics
- `GET /admin/reservations/<cafe_id>` - Get all cafe reservations
- `PUT /admin/reservations/<id>` - Update reservation status
- `GET /admin/tables/<cafe_id>` - Get cafe table management

### System
- `GET /health` - Health check endpoint

## 🔐 Authentication System

### Unified Login
The system uses a single login endpoint that automatically detects whether credentials belong to a user or admin:

\`\`\`javascript
// Login request (works for both users and admins)
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // Important for cookies
  body: JSON.stringify({
    email: 'user@example.com', // or username for admin
    password: 'password123'
  })
});

const data = await response.json();
// Response includes:
// - type: 'user' or 'admin'
// - user/admin: user or admin object
// - message: success message
\`\`\`

### Default Admin Account
- **Username**: `admin`
- **Email**: `admin@barsan.cafe`
- **Password**: `admin123` (change in production!)

## 🗄️ Database Schema

### SQLite WAL Mode Benefits
- **Concurrent Reads**: Multiple processes can read simultaneously
- **Non-blocking Reads**: Reads don't block writes and vice versa
- **Better Performance**: Faster writes and better crash recovery
- **ACID Compliance**: Maintains database integrity

### Main Models
- **User**: Customer accounts with email authentication
- **Admin**: Administrative users with username/email login
- **Cafe**: Restaurant/bar information
- **Zone**: Seating areas within cafes
- **Table**: Individual tables with capacity and status
- **Reservation**: Confirmed table reservations
- **TemporaryReservation**: 15-minute reservation holds
- **Role**: Admin roles and permissions

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key | - | ✅ |
| `JWT_SECRET_KEY` | JWT signing key | - | ✅ |
| `DATABASE_URL` | SQLite database path | `sqlite:///barsan.db` | ❌ |
| `PORT` | Server port | `5000` | ❌ |
| `HOST` | Server host | `0.0.0.0` | ❌ |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` | ❌ |
| `ADMIN_DEFAULT_PASSWORD` | Default admin password | `admin123` | ❌ |
| `SQLITE_WAL_MODE` | Enable WAL mode | `true` | ❌ |

### SQLite Optimization
The application automatically configures SQLite for optimal performance:
- WAL mode for concurrent access
- Increased cache size
- Memory-based temporary storage
- Foreign key constraints enabled

## 🐳 Docker Deployment

### Using Docker Compose
\`\`\`bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
\`\`\`

### Manual Docker Build
\`\`\`bash
# Build image
docker build -t barsan-backend .

# Run container
docker run -p 5000:5000 -v $(pwd)/data:/app/data barsan-backend
\`\`\`

## 🧪 Testing

### Manual API Testing

\`\`\`bash
# Health check
curl http://localhost:5000/health

# User registration
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","fullName":"Test User","phone":"1234567890"}'

# User login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"test@example.com","password":"password123"}'

# Admin login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -c admin_cookies.txt \
  -d '{"email":"admin","password":"admin123"}'

# Get current user
curl -X GET http://localhost:5000/auth/me \
  -b cookies.txt

# Get cafes
curl http://localhost:5000/cafes
\`\`\`

## 📁 Project Structure

\`\`\`
backend/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy database models
├── auth.py             # Authentication routes
├── reservations.py     # Reservation management routes
├── cafes.py           # Cafe and availability routes
├── admin.py           # Admin management routes
├── utils.py           # Utility functions
├── requirements.txt   # Python dependencies
├── run.py            # Application runner
├── Dockerfile        # Docker configuration
├── docker-compose.yml # Docker Compose setup
├── .env.example      # Environment template
├── .gitignore        # Git ignore rules
└── README.md         # This file
\`\`\`

## 🚀 Production Deployment

### 1. Environment Setup
\`\`\`bash
# Set production environment variables
export SECRET_KEY="your-super-secure-secret-key"
export JWT_SECRET_KEY="your-super-secure-jwt-key"
export FLASK_ENV="production"
\`\`\`

### 2. Using Gunicorn
\`\`\`bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
\`\`\`

### 3. Nginx Reverse Proxy (Recommended)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
