from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta, date
import uuid

from models import db, Reservation, TemporaryReservation, Cafe, Table, Zone, User
from utils import (
    generate_reservation_number, 
    is_valid_time_slot, 
    is_time_slot_available,
    validate_email, 
    validate_phone, 
    sanitize_string
)

reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('/temp', methods=['POST'])
def create_temp_reservation():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        cafe_id = data.get('cafeId')
        reservation_date = data.get('date')
        time = data.get('time')
        guests = data.get('guests')
        zone_id = data.get('zoneId')
        session_id = data.get('sessionId')
        
        # Validation
        if not all([cafe_id, reservation_date, time, guests, session_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        if not is_valid_time_slot(time):
            return jsonify({'success': False, 'message': 'Invalid time format'}), 400
        
        if guests < 1 or guests > 20:
            return jsonify({'success': False, 'message': 'Invalid number of guests'}), 400
        
        # Check if cafe exists and is active
        cafe = Cafe.query.filter_by(id=cafe_id, is_active=True).first()
        if not cafe:
            return jsonify({'success': False, 'message': 'Cafe not found or inactive'}), 404
        
        # Parse date
        try:
            reservation_date = datetime.strptime(reservation_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        # Delete existing temp reservation with same session
        TemporaryReservation.query.filter_by(session_id=session_id).delete()
        
        # Create temporary reservation
        temp_reservation = TemporaryReservation(
            id=str(uuid.uuid4()),
            cafe_id=cafe_id,
            date=reservation_date,
            time=time,
            guests=guests,
            zone_id=zone_id,
            session_id=session_id,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        
        db.session.add(temp_reservation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'tempReservation': {
                'id': temp_reservation.id,
                'expiresAt': temp_reservation.expires_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@reservations_bp.route('/', methods=['POST'])
def create_reservation():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        temp_reservation_id = data.get('tempReservationId')
        guest_name = data.get('guestName', '').strip()
        guest_email = data.get('guestEmail', '').lower().strip()
        guest_phone = data.get('guestPhone', '').strip()
        special_requests = data.get('specialRequests', '').strip()
        user_id = data.get('userId')
        
        # Validation
        if not all([temp_reservation_id, guest_name, guest_email, guest_phone]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        if not validate_email(guest_email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        if not validate_phone(guest_phone):
            return jsonify({'success': False, 'message': 'Invalid phone format'}), 400
        
        if len(guest_name) < 2:
            return jsonify({'success': False, 'message': 'Guest name too short'}), 400
        
        # Get temporary reservation
        temp_reservation = TemporaryReservation.query.get(temp_reservation_id)
        if not temp_reservation:
            return jsonify({'success': False, 'message': 'Temporary reservation not found or expired'}), 404
        
        if temp_reservation.expires_at < datetime.utcnow():
            db.session.delete(temp_reservation)
            db.session.commit()
            return jsonify({'success': False, 'message': 'Temporary reservation expired'}), 400
        
        # Check for conflicts with existing reservations
        existing_reservations = Reservation.query.filter(
            Reservation.cafe_id == temp_reservation.cafe_id,
            Reservation.date == temp_reservation.date,
            Reservation.status.in_(['pending', 'confirmed', 'seated'])
        ).all()
        
        existing_times = [{'time': r.time, 'duration': r.duration} for r in existing_reservations]
        
        if not is_time_slot_available(temp_reservation.time, 120, existing_times):
            return jsonify({'success': False, 'message': 'Time slot no longer available'}), 400
        
        # Create reservation
        reservation_number = generate_reservation_number()
        
        reservation = Reservation(
            id=str(uuid.uuid4()),
            reservation_number=reservation_number,
            user_id=user_id,
            cafe_id=temp_reservation.cafe_id,
            guest_name=sanitize_string(guest_name),
            guest_email=guest_email,
            guest_phone=guest_phone.replace('-', '').replace(' ', ''),
            date=temp_reservation.date,
            time=temp_reservation.time,
            guests=temp_reservation.guests,
            special_requests=sanitize_string(special_requests) if special_requests else None,
            status='pending'
        )
        
        db.session.add(reservation)
        
        # Delete temporary reservation
        db.session.delete(temp_reservation)
        db.session.commit()
        
        # Get cafe info for response
        cafe = Cafe.query.get(reservation.cafe_id)
        
        return jsonify({
            'success': True,
            'reservation': {
                'id': reservation.id,
                'reservationNumber': reservation.reservation_number,
                'status': reservation.status,
                'date': reservation.date.isoformat(),
                'time': reservation.time,
                'guests': reservation.guests,
                'cafe': {
                    'name': cafe.name,
                    'displayName': cafe.display_name
                }
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@reservations_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_reservations():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Reservation.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        reservations = query.order_by(Reservation.created_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify({
            'success': True,
            'reservations': [r.to_dict() for r in reservations]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reservations_bp.route('/<reservation_number>', methods=['GET'])
def get_reservation(reservation_number):
    try:
        reservation = Reservation.query.filter_by(reservation_number=reservation_number).first()
        
        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404
        
        return jsonify({
            'success': True,
            'reservation': reservation.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reservations_bp.route('/<reservation_number>', methods=['DELETE'])
def cancel_reservation(reservation_number):
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        email = data.get('email').lower().strip()
        
        reservation = Reservation.query.filter(
            Reservation.reservation_number == reservation_number,
            Reservation.guest_email == email,
            Reservation.status.in_(['pending', 'confirmed'])
        ).first()
        
        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found or cannot be cancelled'}), 404
        
        # Check if cancellation is allowed (at least 2 hours before)
        reservation_datetime = datetime.combine(reservation.date, datetime.strptime(reservation.time, '%H:%M').time())
        two_hours_from_now = datetime.now() + timedelta(hours=2)
        
        if reservation_datetime < two_hours_from_now:
            return jsonify({'success': False, 'message': 'Cannot cancel reservation less than 2 hours before the scheduled time'}), 400
        
        # Update reservation status
        reservation.status = 'cancelled'
        reservation.cancelled_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reservation cancelled successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
