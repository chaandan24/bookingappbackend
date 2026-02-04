"""
Bookings Blueprint
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, limiter
from app.models.booking import Booking, BookingStatus
from app.models.property import Property
from datetime import datetime, date, timedelta
from app.models.blocked_date import BlockedDate

bookings_bp = Blueprint('bookings', __name__)


@bookings_bp.route('/', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new booking"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['property_id', 'check_in', 'check_out', 'guests']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get property
        property = Property.query.get(data['property_id'])
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        # Validate guest count
        if data['guests'] > property.max_guests:
            return jsonify({'error': f'Maximum {property.max_guests} guests allowed for this property'}), 400
        
        # Parse dates
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        
        # Check availability
        if not property.is_available(check_in, check_out):
            return jsonify({'error': 'Property not available for selected dates'}), 400
        
        # Calculate pricing
        pricing = property.calculate_total_price(check_in, check_out)

        host_id = property.host_id
        
        # Create booking
        booking = Booking(
            property_id=data['property_id'],
            guest_id=current_user_id,
            check_in=check_in,
            check_out=check_out,
            guests=data['guests'],
            price_per_night=property.price_per_night,
            nights=pricing['nights'],
            subtotal=pricing['subtotal'],
            cleaning_fee=pricing['cleaning_fee'],
            service_fee=pricing['service_fee'],
            total_price=pricing['total'],
            special_requests=data.get('special_requests'),
            host_id=host_id,
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'message': 'Booking created successfully! Pending approval',
            'booking': booking.to_dict(include_property=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bookings_bp.route('/my-bookings', methods=['GET'])
@jwt_required()
def get_my_bookings():
    """Get current user's bookings"""
    try:
        current_user_id = get_jwt_identity()
        bookings = Booking.query.filter_by(guest_id=current_user_id).all()

    
        today = date.today()
        for booking in bookings:
            if booking.status == 'confirmed' and booking.check_out < today:
                booking.status = 'completed'
    
        db.session.commit()
        
        return jsonify({
            'bookings': [booking.to_dict(include_property=True) for booking in bookings]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bookings_bp.route('/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get booking details"""
    try:
        current_user_id = get_jwt_identity()
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check authorization
        if booking.guest_id != current_user_id and booking.property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'booking': booking.to_dict(include_property=True, include_guest=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        current_user_id = get_jwt_identity()
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check authorization
        if booking.guest_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not booking.can_cancel():
            return jsonify({'error': 'Booking cannot be cancelled'}), 400
        
        data = request.get_json()
        booking.cancel(reason=data.get('reason'))
        
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking': booking.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bookings_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_properties_calendar():
    """Get all properties and calendar availability for the host"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get all properties for this host
        properties = Property.query.filter_by(host_id=current_user_id).all()
        
        if not properties:
            return jsonify({'properties': [], 'calendars': {}}), 200
        
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date required'}), 400
        
        start = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        calendars = {}
        properties_data = []
        
        for property in properties:
            # Get booked dates (include PENDING and COMPLETED, exclude CANCELLED)
            bookings = Booking.query.filter(
                Booking.property_id == property.id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING, BookingStatus.COMPLETED]),
                Booking.check_in < end,
                Booking.check_out > start
            ).all()
            
            booked_dates = []
            for booking in bookings:
                current = booking.check_in
                while current < booking.check_out:
                    booked_dates.append(current.isoformat())
                    current = current + timedelta(days=1)
            
            # Get blocked dates
            blocked_dates_query = BlockedDate.query.filter(
                BlockedDate.property_id == property.id,
                BlockedDate.blocked_date >= start,
                BlockedDate.blocked_date <= end
            ).all()
            
            blocked_dates = [bd.blocked_date.isoformat() for bd in blocked_dates_query]
            
            calendars[str(property.id)] = {
                'booked_dates': booked_dates,
                'blocked_dates': blocked_dates
            }
            
            # Add property data
            properties_data.append({
                'id': property.id,
                'title': property.title,
                'city': property.city,
                'country': property.country,
                'price_per_night': float(property.price_per_night) if property.price_per_night else 0,
                'average_rating': property.average_rating,
                'images': property.images,
                'address': property.address,
                'description': properties.description
            })
        
        return jsonify({
            'properties': properties_data,
            'calendars': calendars
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500