"""
Application Entry Point
Run this file to start the Flask development server
"""

import os
from app import create_app

# Create Flask app instance
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=True)
    
    