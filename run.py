#!/usr/bin/env python3
"""
JobFit Analytics - Main Application Runner
"""

import os
import sys
from app import app, db

def create_tables():
    """Create database tables if they don't exist"""
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        from app import User
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('password123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin/password123")
        
        # Create default settings if not exists
        from app import Settings
        if not Settings.query.first():
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
            print("✅ Default settings created")

def main():
    """Main application entry point"""
    print("🚀 Starting JobFit Analytics...")
    
    # Create database tables
    create_tables()
    
    # Get configuration
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"📊 Application running on http://{host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print("👤 Default admin login: admin/password123")
    print("🛑 Press Ctrl+C to stop")
    
    # Run the application
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n👋 Shutting down JobFit Analytics...")
        sys.exit(0)

if __name__ == '__main__':
    main()
