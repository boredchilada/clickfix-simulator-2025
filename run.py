import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("----------------------------------------------------------------")
    print("WARNING: This tool is for AUTHORIZED SECURITY TESTING ONLY.")
    print("Unauthorized use is illegal. Ensure you have explicit permission.")
    print("----------------------------------------------------------------")
    
    # Only for development, use flask run in production
    ssl_context = ('certs/cert.pem', 'certs/key.pem')
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Check if certs exist, otherwise run without SSL (not recommended for clipboard API)
    if not os.path.exists(ssl_context[0]) or not os.path.exists(ssl_context[1]):
        print("Warning: SSL certificates not found. Clipboard API may not work.")
        ssl_context = None

    app.run(host='0.0.0.0', port=443, ssl_context=ssl_context, debug=debug_mode)