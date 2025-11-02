"""
Bookings Blueprint
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from app.models.booking import Booking, BookingStatus
from app.models.property import Property
from datetime import datetime

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
        
        # Parse dates
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        
        # Check availability
        if not property.is_available(check_in, check_out):
            return jsonify({'error': 'Property not available for selected dates'}), 400
        
        # Calculate pricing
        pricing = property.calculate_total_price(check_in, check_out)
        
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
            special_requests=data.get('special_requests')
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'message': 'Booking created successfully',
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
