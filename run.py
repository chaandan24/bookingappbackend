"""
Application Entry Point
Run this file to start the Flask development server
"""

import os
from app import create_app
from extensions import socketio

# Create Flask app instance
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, debug=debug, host=host, port=port)
    
    # Run the application
    app.run(
        debug=debug,
        host=host,
        port=port
    )
