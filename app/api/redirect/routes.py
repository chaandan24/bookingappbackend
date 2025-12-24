"""
Redirect Routes for Deep Linking
"""

from flask import Blueprint, request

redirect_bp = Blueprint('redirect', __name__)


@redirect_bp.route('/property/<int:property_id>')
def property_landing(property_id):
    """Landing page that redirects to app or store"""
    # Your actual package name and app store IDs
    package_name = 'com.dossdown.app'  # Update this
    app_store_id = 'YOUR_APP_STORE_ID'  # Update when you have iOS
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Property - DossDown</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 400px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }}
            .logo {{
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                border-radius: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 25px;
            }}
            .logo span {{
                font-size: 40px;
            }}
            h1 {{
                color: #1a472a;
                font-size: 24px;
                margin-bottom: 15px;
            }}
            p {{
                color: #666;
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 25px;
            }}
            .spinner {{
                width: 40px;
                height: 40px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #1a472a;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                color: white;
                padding: 14px 30px;
                text-decoration: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                margin: 10px;
                transition: transform 0.2s;
            }}
            .btn:hover {{
                transform: translateY(-2px);
            }}
            .store-buttons {{
                margin-top: 20px;
            }}
            .hidden {{
                display: none;
            }}
        </style>
        <script>
            const propertyId = {property_id};
            const deepLink = "qimbl://property/" + propertyId;
            const playStore = "https://play.google.com/store/apps/details?id={package_name}";
            const appStore = "https://apps.apple.com/app/id{app_store_id}";
            
            function detectPlatform() {{
                const ua = navigator.userAgent.toLowerCase();
                if (ua.includes('android')) return 'android';
                if (/iphone|ipad|ipod/.test(ua)) return 'ios';
                return 'desktop';
            }}
            
            function tryOpenApp() {{
                const platform = detectPlatform();
                
                // Try to open the app
                window.location.href = deepLink;
                
                // Fallback to store after delay
                setTimeout(function() {{
                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('fallback').classList.remove('hidden');
                    
                    if (platform === 'android') {{
                        document.getElementById('play-store-btn').classList.remove('hidden');
                    }} else if (platform === 'ios') {{
                        document.getElementById('app-store-btn').classList.add('hidden');
                    }} else {{
                        document.getElementById('play-store-btn').classList.remove('hidden');
                    }}
                }}, 2000);
            }}
            
            window.onload = tryOpenApp;
        </script>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <span>🏠</span>
            </div>
            
            <div id="loading">
                <h1>Opening DossDown...</h1>
                <div class="spinner"></div>
                <p>Redirecting you to the app</p>
            </div>
            
            <div id="fallback" class="hidden">
                <h1>Get DossDown</h1>
                <p>Download the app to view this property and discover amazing places to stay.</p>
                
                <div class="store-buttons">
                    <a id="play-store-btn" href="https://play.google.com/store/apps/details?id={package_name}" class="btn hidden">
                        📱 Get on Play Store
                    </a>
                    <a id="app-store-btn" href="https://apps.apple.com/app/id{app_store_id}" class="btn hidden">
                        🍎 Get on App Store
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''