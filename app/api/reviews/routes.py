"""
Reviews Blueprint
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from app.models.review import Review
from app.models.booking import Booking, BookingStatus

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/', methods=['POST'])
@jwt_required()
def create_review():
    """Create a review for a property"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['property_id', 'booking_id', 'rating', 'comment']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify booking exists and belongs to user
        booking = Booking.query.get(data['booking_id'])
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.guest_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if booking.status != BookingStatus.COMPLETED:
            return jsonify({'error': 'Can only review completed bookings'}), 400
        
        # Check if review already exists
        existing_review = Review.query.filter_by(
            booking_id=data['booking_id'],
            user_id=current_user_id
        ).first()
        
        if existing_review:
            return jsonify({'error': 'Review already exists for this booking'}), 409
        
        # Create review
        review = Review(
            property_id=data['property_id'],
            user_id=current_user_id,
            booking_id=data['booking_id'],
            rating=data['rating'],
            title=data.get('title'),
            comment=data['comment'],
            cleanliness_rating=data.get('cleanliness_rating'),
            accuracy_rating=data.get('accuracy_rating'),
            location_rating=data.get('location_rating'),
            communication_rating=data.get('communication_rating'),
            check_in_rating=data.get('check_in_rating'),
            value_rating=data.get('value_rating')
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Update property rating
        from app.models.property import Property
        property = Property.query.get(data['property_id'])
        property.update_rating()
        
        return jsonify({
            'message': 'Review created successfully',
            'review': review.to_dict(include_user=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@reviews_bp.route('/property/<int:property_id>', methods=['GET'])
def get_property_reviews(property_id):
    """Get all reviews for a property"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        reviews_query = Review.query.filter_by(
            property_id=property_id,
            is_visible=True
        ).order_by(Review.created_at.desc())
        
        paginated_reviews = reviews_query.paginate(page=page, per_page=per_page, error_out=False)
        
        reviews = [review.to_dict(include_user=True) for review in paginated_reviews.items]
        
        return jsonify({
            'reviews': reviews,
            'total': paginated_reviews.total,
            'pages': paginated_reviews.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reviews_bp.route('/<int:review_id>/response', methods=['POST'])
@jwt_required()
def add_host_response(review_id):
    """Add host response to review"""
    try:
        current_user_id = get_jwt_identity()
        review = Review.query.get(review_id)
        
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        # Check if user is the host
        if review.property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        if 'response' not in data:
            return jsonify({'error': 'response is required'}), 400
        
        review.add_host_response(data['response'])
        
        return jsonify({
            'message': 'Response added successfully',
            'review': review.to_dict(include_user=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
