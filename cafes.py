from flask import Blueprint, request, jsonify
from datetime import datetime, time
import json

from models import db, Cafe, Zone, Table, Reservation
from utils import is_time_slot_available

cafes_bp = Blueprint('cafes', __name__)

@cafes_bp.route('/', methods=['GET'])
def get_cafes():
    try:
        cafes = Cafe.query.filter_by(is_active=True).order_by(Cafe.name).all()
        
        return jsonify({
            'success': True,
            'cafes': [cafe.to_dict() for cafe in cafes]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@cafes_bp.route('/<cafe_id>', methods=['GET'])
def get_cafe(cafe_id):
    try:
        cafe = Cafe.query.filter_by(id=cafe_id, is_active=True).first()
        
        if not cafe:
            return jsonify({'success': False, 'message': 'Cafe not found'}), 404
        
        # Get zones with tables
        zones = Zone.query.filter_by(cafe_id=cafe_id, is_active=True).order_by(Zone.sort_order).all()
        
        cafe_dict = cafe.to_dict()
        cafe_dict['zones'] = []
        
        for zone in zones:
            tables = Table.query.filter_by(
                zone_id=zone.id, 
                is_active=True
            ).order_by(Table.number).all()
            
            zone_dict = zone.to_dict()
            zone_dict['tables'] = []
            
            for table in tables:
                table_dict = {
                    'id': table.id,
                    'number': table.number,
                    'seats': table.seats,
                    'min_guests': table.min_guests,
                    'max_guests': table.max_guests,
                    'features': json.loads(table.features) if table.features else [],
                    'status': table.status
                }
                zone_dict['tables'].append(table_dict)
            
            cafe_dict['zones'].append(zone_dict)
        
        return jsonify({
            'success': True,
            'cafe': cafe_dict
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@cafes_bp.route('/<cafe_id>/availability', methods=['GET'])
def get_availability(cafe_id):
    try:
        # Get query parameters
        date_str = request.args.get('date')
        guests = int(request.args.get('guests', 1))
        
        if not date_str:
            return jsonify({'success': False, 'message': 'Date is required'}), 400
        
        # Parse date
        try:
            reservation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        # Check if cafe exists
        cafe = Cafe.query.filter_by(id=cafe_id, is_active=True).first()
        if not cafe:
            return jsonify({'success': False, 'message': 'Cafe not found'}), 404
        
        # Get existing reservations for the date
        existing_reservations = Reservation.query.filter(
            Reservation.cafe_id == cafe_id,
            Reservation.date == reservation_date,
            Reservation.status.in_(['pending', 'confirmed', 'seated'])
        ).all()
        
        existing_times = [{'time': r.time, 'duration': r.duration} for r in existing_reservations]
        
        # Get suitable tables
        suitable_tables = Table.query.filter(
            Table.cafe_id == cafe_id,
            Table.is_active == True,
            Table.status == 'available',
            Table.min_guests <= guests,
            Table.max_guests >= guests
        ).all()
        
        # Generate time slots (17:00 - 23:00, 30-minute intervals)
        time_slots = []
        for hour in range(17, 24):  # 17:00 to 23:30
            for minute in [0, 30]:
                if hour == 23 and minute > 0:  # Stop at 23:00
                    break
                
                time_str = f"{hour:02d}:{minute:02d}"
                is_available = is_time_slot_available(time_str, 120, existing_times)
                
                time_slots.append({
                    'time': time_str,
                    'available': is_available and len(suitable_tables) > 0,
                    'availableTables': len(suitable_tables) if is_available else 0
                })
        
        # Get zones info
        zones = Zone.query.filter_by(cafe_id=cafe_id, is_active=True).all()
        zones_info = []
        
        for zone in zones:
            zone_tables = [t for t in suitable_tables if t.zone_id == zone.id]
            zones_info.append({
                'id': zone.id,
                'name': zone.name,
                'availableTables': len(zone_tables)
            })
        
        return jsonify({
            'success': True,
            'date': date_str,
            'guests': guests,
            'timeSlots': time_slots,
            'zones': zones_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@cafes_bp.route('/<cafe_id>/zones/<zone_id>/tables', methods=['GET'])
def get_zone_tables(cafe_id, zone_id):
    try:
        # Get query parameters
        date_str = request.args.get('date')
        time_str = request.args.get('time')
        guests = int(request.args.get('guests', 1))
        
        # Build base query
        query = Table.query.filter(
            Table.cafe_id == cafe_id,
            Table.zone_id == zone_id,
            Table.is_active == True,
            Table.min_guests <= guests,
            Table.max_guests >= guests
        )
        
        # If date and time provided, check availability
        if date_str and time_str:
            try:
                reservation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid date format'}), 400
            
            # Get booked tables for this time slot
            existing_reservations = Reservation.query.filter(
                Reservation.cafe_id == cafe_id,
                Reservation.date == reservation_date,
                Reservation.time == time_str,
                Reservation.status.in_(['pending', 'confirmed', 'seated']),
                Reservation.table_id.isnot(None)
            ).all()
            
            booked_table_ids = [r.table_id for r in existing_reservations]
            
            if booked_table_ids:
                query = query.filter(~Table.id.in_(booked_table_ids))
        
        tables = query.order_by(Table.number).all()
        
        tables_data = []
        for table in tables:
            table_dict = {
                'id': table.id,
                'number': table.number,
                'seats': table.seats,
                'min_guests': table.min_guests,
                'max_guests': table.max_guests,
                'location': table.location,
                'features': json.loads(table.features) if table.features else [],
                'zone': table.zone.name,
                'available': table.status == 'available'
            }
            tables_data.append(table_dict)
        
        return jsonify({
            'success': True,
            'tables': tables_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
