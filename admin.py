from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date
from sqlalchemy import func
from functools import wraps

from models import db, Admin, Cafe, Reservation, Table, Zone, AdminRole, Role

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        claims = get_jwt()
        if claims.get('type') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def check_cafe_access(admin_id, cafe_id):
    """Check if admin has access to the specified cafe"""
    admin_role = AdminRole.query.filter_by(admin_id=admin_id, cafe_id=cafe_id).first()
    return admin_role is not None

@admin_bp.route('/dashboard/<cafe_id>', methods=['GET'])
@admin_required
def get_dashboard(cafe_id):
    try:
        admin_id = get_jwt_identity()
        
        # Check if admin has access to this cafe
        if not check_cafe_access(admin_id, cafe_id):
            return jsonify({'success': False, 'message': 'Access denied to this cafe'}), 403
        
        today = date.today()
        
        # Get today's stats
        today_reservations = Reservation.query.filter(
            Reservation.cafe_id == cafe_id,
            Reservation.date == today
        ).count()
        
        pending_reservations = Reservation.query.filter(
            Reservation.cafe_id == cafe_id,
            Reservation.status == 'pending'
        ).count()
        
        available_tables = Table.query.filter(
            Table.cafe_id == cafe_id,
            Table.is_active == True,
            Table.status == 'available'
        ).count()
        
        total_tables = Table.query.filter(
            Table.cafe_id == cafe_id,
            Table.is_active == True
        ).count()
        
        # Get recent reservations
        recent_reservations = Reservation.query.filter(
            Reservation.cafe_id == cafe_id
        ).order_by(Reservation.created_at.desc()).limit(10).all()
        
        recent_reservations_data = []
        for r in recent_reservations:
            reservation_dict = {
                'id': r.id,
                'reservation_number': r.reservation_number,
                'guest_name': r.guest_name,
                'date': r.date.isoformat(),
                'time': r.time,
                'guests': r.guests,
                'status': r.status,
                'table': None,
                'created_at': r.created_at.isoformat()
            }
            
            if r.table:
                reservation_dict['table'] = {
                    'number': r.table.number,
                    'zone': r.table.zone.name
                }
            
            recent_reservations_data.append(reservation_dict)
        
        return jsonify({
            'success': True,
            'stats': {
                'todayReservations': today_reservations,
                'pendingReservations': pending_reservations,
                'availableTables': available_tables,
                'totalTables': total_tables
            },
            'recentReservations': recent_reservations_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/reservations/<cafe_id>', methods=['GET'])
@admin_required
def get_reservations(cafe_id):
    try:
        admin_id = get_jwt_identity()
        
        # Check access
        if not check_cafe_access(admin_id, cafe_id):
            return jsonify({'success': False, 'message': 'Access denied to this cafe'}), 403
        
        # Get query parameters
        status = request.args.get('status')
        date_str = request.args.get('date')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Reservation.query.filter_by(cafe_id=cafe_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                query = query.filter_by(date=target_date)
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        total = query.count()
        reservations = query.order_by(Reservation.created_at.desc()).offset(offset).limit(limit).all()
        
        reservations_data = []
        for r in reservations:
            reservation_dict = {
                'id': r.id,
                'reservation_number': r.reservation_number,
                'guest_name': r.guest_name,
                'guest_email': r.guest_email,
                'guest_phone': r.guest_phone,
                'date': r.date.isoformat(),
                'time': r.time,
                'guests': r.guests,
                'status': r.status,
                'special_requests': r.special_requests,
                'table': None,
                'created_at': r.created_at.isoformat()
            }
            
            if r.table:
                reservation_dict['table'] = {
                    'id': r.table.id,
                    'number': r.table.number,
                    'zone': r.table.zone.name
                }
            
            reservations_data.append(reservation_dict)
        
        return jsonify({
            'success': True,
            'reservations': reservations_data,
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/reservations/<reservation_id>', methods=['PUT'])
@admin_required
def update_reservation(reservation_id):
    try:
        admin_id = get_jwt_identity()
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404
        
        # Check access
        if not check_cafe_access(admin_id, reservation.cafe_id):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Update fields
        status = data.get('status')
        table_id = data.get('tableId')
        notes = data.get('notes')
        
        old_status = reservation.status
        
        if status:
            reservation.status = status
            
            if status == 'confirmed' and not reservation.confirmed_at:
                reservation.confirmed_at = datetime.utcnow()
            elif status == 'seated' and not reservation.seated_at:
                reservation.seated_at = datetime.utcnow()
            elif status == 'completed' and not reservation.completed_at:
                reservation.completed_at = datetime.utcnow()
            elif status == 'cancelled' and not reservation.cancelled_at:
                reservation.cancelled_at = datetime.utcnow()
        
        if table_id:
            reservation.table_id = table_id
        
        if notes:
            reservation.notes = notes
        
        reservation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reservation': reservation.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/tables/<cafe_id>', methods=['GET'])
@admin_required
def get_tables(cafe_id):
    try:
        admin_id = get_jwt_identity()
        
        # Check access
        if not check_cafe_access(admin_id, cafe_id):
            return jsonify({'success': False, 'message': 'Access denied to this cafe'}), 403
        
        tables = Table.query.filter_by(cafe_id=cafe_id).order_by(Table.number).all()
        
        tables_data = []
        for t in tables:
            table_dict = {
                'id': t.id,
                'number': t.number,
                'seats': t.seats,
                'min_guests': t.min_guests,
                'max_guests': t.max_guests,
                'location': t.location,
                'features': json.loads(t.features) if t.features else [],
                'status': t.status,
                'is_active': t.is_active,
                'zone': {
                    'id': t.zone.id,
                    'name': t.zone.name
                }
            }
            tables_data.append(table_dict)
        
        return jsonify({
            'success': True,
            'tables': tables_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
