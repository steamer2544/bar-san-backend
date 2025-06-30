import re
import random
import string
from datetime import datetime, time

def generate_reservation_number():
    """Generate a unique reservation number"""
    timestamp = str(int(datetime.now().timestamp()))[-6:]
    random_chars = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"RSV{timestamp}{random_chars}"

def is_valid_time_slot(time_str):
    """Validate time format (HH:MM)"""
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))

def time_to_minutes(time_str):
    """Convert time string to minutes since midnight"""
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

def is_time_slot_available(requested_time, duration, existing_reservations):
    """Check if a time slot is available"""
    requested_start = time_to_minutes(requested_time)
    requested_end = requested_start + duration
    
    for reservation in existing_reservations:
        existing_start = time_to_minutes(reservation['time'])
        existing_end = existing_start + reservation['duration']
        
        # Check for overlap
        if (requested_start >= existing_start and requested_start < existing_end) or \
           (requested_end > existing_start and requested_end <= existing_end) or \
           (requested_start <= existing_start and requested_end >= existing_end):
            return False
    
    return True

def validate_email(email):
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """Validate phone format"""
    # Remove spaces and dashes
    clean_phone = phone.replace('-', '').replace(' ', '')
    pattern = r'^[0-9]{9,10}$'
    return bool(re.match(pattern, clean_phone))

def sanitize_string(text):
    """Sanitize string input"""
    if not text:
        return text
    # Remove HTML tags and trim whitespace
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text.strip()

def add_minutes_to_time(time_str, minutes):
    """Add minutes to a time string"""
    hours, mins = map(int, time_str.split(':'))
    total_minutes = hours * 60 + mins + minutes
    new_hours = (total_minutes // 60) % 24
    new_mins = total_minutes % 60
    return f"{new_hours:02d}:{new_mins:02d}"
