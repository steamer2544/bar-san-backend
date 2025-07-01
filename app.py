from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
from sqlalchemy import text

from models import db, User, Cafe, Zone, Table, Reservation, TemporaryReservation, Admin, Role, AdminRole
from auth import auth_bp
from reservations import reservations_bp
from cafes import cafes_bp
from admin import admin_bp
from utils import generate_reservation_number, is_valid_time_slot, validate_email, validate_phone

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'barsan-secret-key-2024')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///barsan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app, origins=os.getenv('FRONTEND_URL', '*'), supports_credentials=True)

# Add this after the CORS initialization
def configure_database():
    """Configure database settings"""
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        with db.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA cache_size=10000"))
            conn.execute(text("PRAGMA temp_store=MEMORY"))
            conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB
            conn.commit()
        print("SQLite configured with WAL mode and optimizations")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(reservations_bp, url_prefix='/reservations')
app.register_blueprint(cafes_bp, url_prefix='/cafes')
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    return jsonify({'message': 'BarSan API is running!', 'status': 'ok'})

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected'
    })

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad Request',
        'message': str(error.description)
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'Insufficient permissions'
    }), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': 'Something went wrong'
    }), 500

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

def seed_data():
    """Seed initial data"""
    with app.app_context():
        # Create cafes
        if not Cafe.query.filter_by(name='BarSan').first():
            barsan = Cafe(
                name='BarSan',
                display_name='BarSan.',
                description='BarSan Cafe',
                address='123 Main St',
                phone='02-123-4567',
                opening_hours=json.dumps({'monday': {'open': '17:00', 'close': '02:00'}}),
                is_active=True
            )
            db.session.add(barsan)
            print("Initial data barsan successfully")

        if not Cafe.query.filter_by(name='NOIR').first():
            noir = Cafe(
                name='NOIR',
                display_name='N O I R',
                description='NOIR Cafe',
                address='456 Oak St',
                phone='02-765-4321',
                opening_hours=json.dumps({'monday': {'open': '17:00', 'close': '02:00'}}),
                is_active=True
            )
            db.session.add(noir)
            print("Initial data noir successfully")

        db.session.commit()

        # Create zones and tables
        barsan_cafe = Cafe.query.filter_by(name='BarSan').first()
        if barsan_cafe and not Zone.query.filter_by(cafe_id=barsan_cafe.id).first():
            zone_a = Zone(
                cafe_id=barsan_cafe.id,
                name='Zone A',
                description='Main dining area',
                capacity=20,
                is_active=True
            )
            db.session.add(zone_a)
            db.session.commit()
            print("Initial data zones and tables successfully")

            # Add tables to Zone A
            for i in range(1, 11):
                table = Table(
                    cafe_id=barsan_cafe.id,
                    zone_id=zone_a.id,
                    number=i,
                    seats=4,
                    min_guests=1,
                    max_guests=4,
                    location='Main area',
                    features=json.dumps(['standard']),
                    status='available',
                    is_active=True
                )
                db.session.add(table)

        # Create admin roles
        if not Role.query.filter_by(name='super_admin').first():
            super_admin_role = Role(
                name='super_admin',
                display_name='Super Admin',
                description='Full access to all cafes',
                permissions=json.dumps({'all': True}),
                is_system=True
            )
            db.session.add(super_admin_role)

            admin_role = Role(
                name='admin',
                display_name='Admin',
                description='Full access to assigned cafe',
                permissions=json.dumps({
                    'manage_reservations': True,
                    'manage_tables': True,
                    'view_reports': True
                })
            )
            db.session.add(admin_role)
            print("Initial data admin roles successfully")

        db.session.commit()

        # Create admin user
        if not Admin.query.filter_by(username='admin').first():
            admin_user = Admin(
                username='admin',
                email='admin@barsan.cafe',
                password_hash=generate_password_hash('admin123'),
                full_name='System Admin',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()

            # Assign super admin role
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            admin_role_assignment = AdminRole(
                admin_id=admin_user.id,
                role_id=super_admin_role.id,
                cafe_id=barsan_cafe.id
            )
            db.session.add(admin_role_assignment)
            print("Initial data admin user successfully")

        db.session.commit()
        print("Initial data seeded successfully")

if __name__ == '__main__':
    create_tables()
    seed_data()
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
