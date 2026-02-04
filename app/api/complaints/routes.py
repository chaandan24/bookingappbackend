from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.complaint import Complaint
from extensions import db

complaints_bp = Blueprint('complaints', __name__)

@complaints_bp.route('', methods=['POST'])
@jwt_required()
def submit_complaint():
    """Submit a new complaint"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        category = data.get('category')
        subject = data.get('subject')
        description = data.get('description')
        
        if not all([category, subject, description]):
            return jsonify({'error': 'Category, subject, and description are required'}), 400
        
        if len(subject.strip()) < 5:
            return jsonify({'error': 'Subject must be at least 5 characters'}), 400
            
        if len(description.strip()) < 20:
            return jsonify({'error': 'Description must be at least 20 characters'}), 400
        
        complaint = Complaint(
            user_id=current_user_id,
            category=category,
            subject=subject.strip(),
            description=description.strip(),
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        return jsonify({
            'message': 'Complaint submitted successfully',
            'complaint': complaint.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500