# BarSan Flask Backend

A Flask-based REST API for the BarSan table reservation system using SQLAlchemy and SQLite with WAL mode for optimal performance.

## 🚀 Features

  - **Unified Authentication**: Single login endpoint for both users and admins.
  - **SQLite WAL Mode**: Write-Ahead Logging for high-concurrency access without blocking.
  - **JWT Authentication**: Secure, cookie-based token authentication.
  - **Reservation System**: Complete reservation management, including temporary holds.
  - **Admin Dashboard**: Interface for managing reservations and cafe settings.
  - **CORS Support**: Ready for frontend integration.
  - **Docker Ready**: Fully containerized for easy deployment.
  - **Auto Database Setup**: Automatic database creation and data seeding on first run.

## 🛠️ Tech Stack

  - **Framework**: Flask (Python)
  - **ORM**: SQLAlchemy
  - **Database**: SQLite with WAL mode
  - **Authentication**: Flask-JWT-Extended
  - **Password Hashing**: Werkzeug
  - **Deployment**: Gunicorn, Docker
  - **Environment**: python-dotenv

## 📁 Project Structure

```
backend/
├── app.py              # Main Flask application factory and blueprint setup
├── models.py           # SQLAlchemy database models
├── auth.py             # Authentication routes
├── reservations.py     # Reservation management routes
├── cafes.py            # Cafe and availability routes
├── admin.py            # Admin management routes
├── utils.py            # Utility functions
├── run.py              # Entry point for development server (python run.py)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
├── .env.example        # Environment variable template
└── README.md           # This file
```

-----

## 🚀 Getting Started (Local Development)

### Prerequisites

  - Python 3.8+
  - pip (Python package manager)
  - A virtual environment tool (like `venv`)

### 1\. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd backend

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2\. Configure Environment Variables

```bash
# Create a .env file from the template
cp .env.example .env
```

Now, open the `.env` file and edit the variables. At a minimum, **you must change `SECRET_KEY` and `JWT_SECRET_KEY` to new, random, and secure values.**

> ⚠️ **Security Warning:** The `.env` file contains sensitive credentials. Ensure it is listed in your `.gitignore` and **never** commit it to version control.

### 3\. Run the Development Server

```bash
# Start the application
python run.py
```

The API will now be available at `http://localhost:5000`.

> ⚠️ This command starts a **development server**. It is perfect for local testing but is **not suitable for production use**. For production, please follow the deployment instructions below.

-----

## 🐳 Deployment (Production)

### 1\. Production Configuration

For production, ensure your `.env` file is configured correctly:

  - `SECRET_KEY` and `JWT_SECRET_KEY` must be set to strong, unique values.
  - `ADMIN_DEFAULT_PASSWORD` should be changed from `admin123`.
  - `FRONTEND_URL` should point to your live frontend application's URL.

### 2\. Option A: Docker & Docker Compose (Recommended)

Using Docker is the easiest way to deploy the application.

```bash
# Build and run all services in the background
docker-compose up --build -d

# View application logs
docker-compose logs -f

# Stop and remove containers
docker-compose down
```

### 3\. Option B: Manual with Gunicorn & Nginx

For a traditional deployment on a virtual server.

#### Step 1: Install Gunicorn

If you followed the development setup, Gunicorn should already be installed from `requirements.txt`. If not:

```bash
pip install gunicorn
```

#### Step 2: Run with Gunicorn

Gunicorn is a robust WSGI server for running Python web applications in production.

```bash
# Run the app with 4 worker processes on port 5000
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```

#### Step 3: Use Nginx as a Reverse Proxy (Recommended)

It's best practice to place your Gunicorn server behind a reverse proxy like Nginx to handle incoming traffic, SSL termination, and serving static files.

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000; # Points to the Gunicorn process
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

-----

## 🌐 API Endpoints

### Authentication (Unified)

  - `POST /auth/login` - Login for both users and admins.
  - `POST /auth/register` - User registration.
  - `GET /auth/me` - Get current user/admin info.
  - `POST /auth/logout` - Logout (clears auth cookie).

### Reservations

  - `POST /reservations/temp` - Create temporary reservation (15-min hold).
  - `POST /reservations` - Create confirmed reservation.
  - `GET /reservations/my` - Get user's reservations.
  - `GET /reservations/<number>` - Get reservation details.
  - `DELETE /reservations/<number>` - Cancel reservation.

### Cafes

  - `GET /cafes` - Get all active cafes.
  - `GET /cafes/<id>` - Get cafe details.
  - `GET /cafes/<id>/availability` - Get available time slots.
  - `GET /cafes/<id>/zones/<zone_id>/tables` - Get tables in a zone.

### Admin (requires admin auth)

  - `GET /admin/dashboard/<cafe_id>` - Get dashboard statistics.
  - `GET /admin/reservations/<cafe_id>` - Get all cafe reservations.
  - `PUT /admin/reservations/<id>` - Update reservation status.
  - `GET /admin/tables/<cafe_id>` - Get cafe table management.

### System

  - `GET /health` - Health check endpoint.

-----

## 🔐 Authentication System

### Unified Login

The system uses a single login endpoint. It automatically detects if the credentials belong to a **user** (by email) or an **admin** (by username or email).

```javascript
// Example login request
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // Important for sending/receiving cookies
  body: JSON.stringify({
    email: 'user@example.com', // or 'admin' for admin username
    password: 'password123'
  })
});
const data = await response.json();
// data.type will be 'user' or 'admin'
```

### Default Admin Account

  - **Username**: `admin`
  - **Email**: `admin@barsan.cafe`
  - **Password**: `admin123` (Change this in `.env` for production\!)

-----

## 🗄️ Database Schema

### SQLite WAL Mode Benefits

  - **Concurrent Reads/Writes**: Multiple clients can read the database while one is writing, preventing blocks.
  - **Better Performance**: Significantly faster write operations.
  - **ACID Compliance**: Maintains data integrity and reliability.

### Main Models

  - **User**: Customer accounts.
  - **Admin**: Administrative users.
  - **Cafe**: Restaurant/bar information.
  - **Zone**: Seating areas within a cafe.
  - **Table**: Individual tables.
  - **Reservation**: Confirmed table reservations.
  - **TemporaryReservation**: 15-minute reservation holds.

-----

## 🧪 Testing

Use `curl` or any API client to test the endpoints.

```bash
# Health check
curl http://localhost:5000/health

# Register a new user
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","fullName":"Test User","phone":"1234567890"}'

# Login as a user (this saves the auth cookie to cookies.txt)
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" -c cookies.txt \
  -d '{"email":"test@example.com","password":"password123"}'

# Get current user info using the saved cookie
curl http://localhost:5000/auth/me -b cookies.txt
```