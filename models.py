from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

# Configure SQLite for WAL mode and performance
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Optimize SQLite performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    email_verified = db.Column(db.DateTime)
    full_name = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    image = db.Column(db.String(500))
    password_hash = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    preferences = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    temp_reservations = db.relationship('TemporaryReservation', backref='user', lazy=True)

    @property
    def preferences_dict(self):
        return json.loads(self.preferences) if self.preferences else {}
    
    @preferences_dict.setter
    def preferences_dict(self, value):
        self.preferences = json.dumps(value) if value else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'image': self.image,
            'is_verified': self.is_verified,
            'email_verified': self.email_verified.isoformat() if self.email_verified else None,
            'preferences': json.loads(self.preferences) if self.preferences else None,
            'created_at': self.created_at.isoformat()
        }

class Cafe(db.Model):
    __tablename__ = 'cafes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    website = db.Column(db.String(500))
    image = db.Column(db.String(500))
    opening_hours = db.Column(db.Text)  # JSON string
    is_active = db.Column(db.Boolean, default=True)
    settings = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    zones = db.relationship('Zone', backref='cafe', lazy=True, cascade='all, delete-orphan')
    tables = db.relationship('Table', backref='cafe', lazy=True, cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='cafe', lazy=True)
    temp_reservations = db.relationship('TemporaryReservation', backref='cafe', lazy=True)
    admin_roles = db.relationship('AdminRole', backref='cafe', lazy=True)

    @property
    def opening_hours_dict(self):
        return json.loads(self.opening_hours) if self.opening_hours else {}
    
    @opening_hours_dict.setter
    def opening_hours_dict(self, value):
        self.opening_hours = json.dumps(value) if value else None
    
    @property
    def settings_dict(self):
        return json.loads(self.settings) if self.settings else {}
    
    @settings_dict.setter
    def settings_dict(self, value):
        self.settings = json.dumps(value) if value else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'image': self.image,
            'opening_hours': json.loads(self.opening_hours) if self.opening_hours else None,
            'is_active': self.is_active
        }

class Zone(db.Model):
    __tablename__ = 'zones'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cafe_id = db.Column(db.String(36), db.ForeignKey('cafes.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tables = db.relationship('Table', backref='zone', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'capacity': self.capacity,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }

class Table(db.Model):
    __tablename__ = 'tables'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cafe_id = db.Column(db.String(36), db.ForeignKey('cafes.id'), nullable=False)
    zone_id = db.Column(db.String(36), db.ForeignKey('zones.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    min_guests = db.Column(db.Integer, default=1)
    max_guests = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255))
    features = db.Column(db.Text)  # JSON array as string
    status = db.Column(db.String(50), default='available')
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='table', lazy=True)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('cafe_id', 'number', name='unique_cafe_table_number'),)

    @property
    def features_list(self):
        return json.loads(self.features) if self.features else []
    
    @features_list.setter
    def features_list(self, value):
        self.features = json.dumps(value) if value else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'seats': self.seats,
            'min_guests': self.min_guests,
            'max_guests': self.max_guests,
            'location': self.location,
            'features': json.loads(self.features) if self.features else [],
            'status': self.status,
            'is_active': self.is_active,
            'zone': self.zone.to_dict() if self.zone else None
        }

class TemporaryReservation(db.Model):
    __tablename__ = 'temporary_reservations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    cafe_id = db.Column(db.String(36), db.ForeignKey('cafes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    zone_id = db.Column(db.String(36), db.ForeignKey('zones.id'))
    table_id = db.Column(db.String(36), db.ForeignKey('tables.id'))
    session_id = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reservation_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    cafe_id = db.Column(db.String(36), db.ForeignKey('cafes.id'), nullable=False)
    table_id = db.Column(db.String(36), db.ForeignKey('tables.id'))
    
    # Guest information
    guest_name = db.Column(db.String(255), nullable=False)
    guest_email = db.Column(db.String(255), nullable=False)
    guest_phone = db.Column(db.String(20), nullable=False)
    
    # Reservation details
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, default=120)  # minutes
    status = db.Column(db.String(50), default='pending')
    
    # Additional information
    special_requests = db.Column(db.Text)
    notes = db.Column(db.Text)
    source = db.Column(db.String(50), default='website')
    
    # Timestamps
    confirmed_at = db.Column(db.DateTime)
    seated_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'reservation_number': self.reservation_number,
            'guest_name': self.guest_name,
            'guest_email': self.guest_email,
            'guest_phone': self.guest_phone,
            'date': self.date.isoformat(),
            'time': self.time,
            'guests': self.guests,
            'duration': self.duration,
            'status': self.status,
            'special_requests': self.special_requests,
            'notes': self.notes,
            'source': self.source,
            'cafe': self.cafe.to_dict() if self.cafe else None,
            'table': self.table.to_dict() if self.table else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'seated_at': self.seated_at.isoformat() if self.seated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('AdminRole', backref='admin', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat()
        }

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.Text, nullable=False)  # JSON string
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin_roles = db.relationship('AdminRole', backref='role', lazy=True)

    @property
    def permissions_dict(self):
        return json.loads(self.permissions) if self.permissions else {}
    
    @permissions_dict.setter
    def permissions_dict(self, value):
        self.permissions = json.dumps(value) if value else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'permissions': json.loads(self.permissions) if self.permissions else {},
            'is_system': self.is_system
        }

class AdminRole(db.Model):
    __tablename__ = 'admin_roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = db.Column(db.String(36), db.ForeignKey('admins.id'), nullable=False)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=False)
    cafe_id = db.Column(db.String(36), db.ForeignKey('cafes.id'), nullable=False)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('admin_id', 'role_id', 'cafe_id', name='unique_admin_role_cafe'),)

