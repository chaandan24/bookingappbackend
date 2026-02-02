"""
Property Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, limiter
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.user import User, UserRole
from datetime import datetime
from app.api.upload.routes import upload_property_images_internal
from app.services.s3_service import S3Service

properties_bp = Blueprint('properties', __name__)


@properties_bp.route('/', methods=['GET'])
@limiter.limit("100 per hour")
def get_properties():
    """Get all properties with filters"""
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filters
        city = request.args.get('city')
        country = request.args.get('country')
        property_type = request.args.get('property_type')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        bedrooms = request.args.get('bedrooms', type=int)
        guests = request.args.get('guests', type=int)
        host_id = request.args.get('host_id', type=int)
        amenities = request.args.getlist('amenities')  # NEW: Get list of amenities
        
        # Build query
        query = Property.query.filter_by(status=PropertyStatus.ACTIVE)

        if host_id:
            query = query.filter(Property.host_id == host_id)
        
        if city:
            query = query.filter(Property.city.ilike(f'%{city}%'))
        
        if country:
            query = query.filter(Property.country.ilike(f'%{country}%'))
        
        if property_type:
            query = query.filter_by(property_type=PropertyType(property_type))
        
        if min_price:
            query = query.filter(Property.price_per_night >= min_price)
        
        if max_price:
            query = query.filter(Property.price_per_night <= max_price)
        
        if bedrooms:
            query = query.filter(Property.bedrooms >= bedrooms)
        
        if guests:
            query = query.filter(Property.max_guests >= guests)
        
        # NEW: Filter by amenities
        if amenities:
            for amenity in amenities:
                query = query.filter(Property.amenities.contains(amenity))
        
        # Sort
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'price':
            query = query.order_by(Property.price_per_night.desc() if sort_order == 'desc' else Property.price_per_night.asc())
        elif sort_by == 'rating':
            query = query.order_by(Property.average_rating.desc() if sort_order == 'desc' else Property.average_rating.asc())
        else:
            query = query.order_by(Property.created_at.desc() if sort_order == 'desc' else Property.created_at.asc())
        
        # Paginate
        paginated_properties = query.paginate(page=page, per_page=per_page, error_out=False)
        
        properties = [prop.to_dict(include_host=True, include_calendar=True) for prop in paginated_properties.items]
        
        return jsonify({
            'properties': properties,
            'total': paginated_properties.total,
            'pages': paginated_properties.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/<int:property_id>', methods=['GET'])
@limiter.limit("100 per hour")
def get_property(property_id):
    """Get single property by ID"""
    try:
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        # Increment view count
        property.increment_views()
        
        return jsonify({
            'property': property.to_dict(include_host=True, include_calendar=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/create_property', methods=['POST'])
@jwt_required()
@limiter.limit("10 per day")
def create_property():
    """Create a new property listing"""
    try:
        current_user_id = get_jwt_identity()
        data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['title', 'description', 'property_type', 'address', 
                          'city', 'country', 'bedrooms', 'bathrooms', 
                          'max_guests', 'price_per_night']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        images_urls = []
        try: 
            if 'images' in request.files or any(key.startswith('images[') for key in request.files):
                images_urls = upload_property_images_internal(request=request, jwt_identity=current_user_id)
            else: 
                images_urls = ['']
        except Exception as e:
            print(f'Upload error: {str(e)}')
            S3Service.delete_multiple_files(images_urls)
            return jsonify({'error': f'Image upload failed: {str(e)}'}), 400
        
        # Create property
        property = Property(
            host_id=current_user_id,
            title=data['title'],
            description=data['description'],
            property_type=PropertyType(data['property_type']),
            address=data['address'],
            city=data['city'],
            state=data.get('state'),
            country=data['country'],
            postal_code=data.get('postal_code'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            bedrooms=data['bedrooms'],
            bathrooms=data['bathrooms'],
            max_guests=data['max_guests'],
            square_feet=data.get('square_feet'),
            price_per_night=data['price_per_night'],
            cleaning_fee=data.get('cleaning_fee', 0),
            amenities=data.get('amenities', []),
            min_nights=data.get('min_nights', 1),
            max_nights=data.get('max_nights'),
            cancellation_policy=data.get('cancellation_policy', 'flexible'),
            images = {
                'description': data.get('description', ''),
                'images_urls': images_urls
            },
            available=data['available']
        )
        
        db.session.add(property)
        db.session.commit()
        
        return jsonify({
            'message': 'Property created successfully',
            'property': property.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/<int:property_id>/update', methods=['PUT'])
@jwt_required()
def update_property(property_id):
    """Update property (host only)"""
    try:
        current_user_id = int(get_jwt_identity())
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        # Check if user is the host
        if property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update fields
        updateable_fields = ['title', 'description', 'address', 'city', 'state', 
                            'country', 'postal_code', 'bedrooms', 'bathrooms', 
                            'max_guests', 'square_feet', 'price_per_night', 
                            'cleaning_fee', 'amenities', 'min_nights', 'max_nights',
                            'cancellation_policy', 'images', 'status', 'available']
        
        for field in updateable_fields:
            if field in data:
                if field == 'status':
                    setattr(property, field, PropertyStatus(data[field]))
                elif field == 'property_type':
                    setattr(property, field, PropertyType(data[field]))
                else:
                    setattr(property, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Property updated successfully',
            'property': property.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/<int:property_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_property(property_id):
    """Delete property (host only)"""
    try:
        current_user_id = int(get_jwt_identity())
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        if property.host_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(property)
        db.session.commit()
        
        return jsonify({
            'message': 'Property deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/<int:property_id>/availability', methods=['GET'])
def check_availability(property_id):
    """Check if property is available for given dates"""
    try:
        property = Property.query.get(property_id)
        
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        check_in_str = request.args.get('check_in')
        check_out_str = request.args.get('check_out')
        
        if not check_in_str or not check_out_str:
            return jsonify({'error': 'check_in and check_out dates are required'}), 400
        
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        is_available = property.is_available(check_in, check_out)
        
        pricing = None
        if is_available:
            pricing = property.calculate_total_price(check_in, check_out)
        
        return jsonify({
            'available': is_available,
            'pricing': pricing
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/my-properties', methods=['GET'])
@jwt_required()
def get_my_properties():
    """Get current user's properties"""
    try:
        current_user_id = get_jwt_identity()
        properties = Property.query.filter_by(host_id=current_user_id).all()
        
        return jsonify({
            'properties': [prop.to_dict() for prop in properties]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/nearby', methods=['GET'])
@limiter.limit("100 per hour")
def get_nearby_properties():
    """Get properties in user's city and nearby cities"""
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Required: user's current city
        user_city = request.args.get('city')
        user_country = request.args.get('country')
        
        if not user_city:
            return jsonify({'error': 'city parameter is required'}), 400
        
        # Build query for properties in the same city/country
        query = Property.query.filter_by(status=PropertyStatus.ACTIVE)
        
        if user_country:
            # Prioritize same country
            query = query.filter(Property.country.ilike(f'%{user_country}%'))
        
        # Find properties in the same city or nearby
        # Using ILIKE for case-insensitive search
        query = query.filter(Property.city.ilike(f'%{user_city}%'))
        
        # Sort by rating and recency
        query = query.order_by(
            Property.average_rating.desc(),
            Property.created_at.desc()
        )
        
        # Paginate
        paginated_properties = query.paginate(page=page, per_page=per_page, error_out=False)
        
        properties = [prop.to_dict(include_host=True) for prop in paginated_properties.items]
        
        return jsonify({
            'properties': properties,
            'total': paginated_properties.total,
            'pages': paginated_properties.pages,
            'current_page': page,
            'per_page': per_page,
            'location': {
                'city': user_city,
                'country': user_country
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@properties_bp.route('/explore', methods=['GET'])
@limiter.limit("100 per hour")
def get_explore_properties():
    """Get curated properties for explore page - grouped by random cities"""
    try:
        from sqlalchemy import func
        
        cities = db.session.query(Property.city).filter(
            Property.status == PropertyStatus.ACTIVE
        ).distinct().all()
        
        if not cities:
            return jsonify({'city_groups': []}), 200
        
        city_names = [c[0] for c in cities if c[0]]
        import random
        selected_cities = random.sample(city_names, min(10, len(city_names)))
        
        city_groups = []
        for city in selected_cities:
            properties = Property.query.filter(
                Property.status == PropertyStatus.ACTIVE,
                Property.city == city
            ).order_by(
                Property.average_rating.desc(),
                Property.view_count.desc()
            ).all()
            
            if properties:
                city_groups.append({
                    'city': city,
                    'properties': [prop.to_dict(include_host=True) for prop in properties]
                })
        
        return jsonify({
            'city_groups': city_groups,
            'total_cities': len(city_groups)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@properties_bp.route('/bounds', methods=['GET'])
@limiter.limit("100 per hour")
def get_properties_in_bounds():
    """Get properties within map coordinate bounds"""
    try:
        min_lat = request.args.get('min_lat', type=float)
        max_lat = request.args.get('max_lat', type=float)
        min_lng = request.args.get('min_lng', type=float)
        max_lng = request.args.get('max_lng', type=float)
        
        if None in [min_lat, max_lat, min_lng, max_lng]:
            return jsonify({'error': 'min_lat, max_lat, min_lng, and max_lng are required'}), 400
        
        query = Property.query.filter(
            Property.status == PropertyStatus.ACTIVE,
            Property.latitude.isnot(None),
            Property.longitude.isnot(None),
            Property.latitude.between(min_lat, max_lat),
            Property.longitude.between(min_lng, max_lng)
        ).order_by(
            Property.average_rating.desc()
        ).limit(100)  # Limit to prevent overload
        
        properties = [prop.to_dict(include_host=True) for prop in query.all()]
        
        return jsonify({
            'properties': properties,
            'count': len(properties),
            'bounds': {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lng': min_lng,
                'max_lng': max_lng
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500