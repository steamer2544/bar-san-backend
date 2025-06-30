import os
from app import app, create_tables, seed_data, configure_database

if __name__ == '__main__':
    with app.app_context():
        configure_database()
        create_tables()
        seed_data()

    debug = os.getenv('FLASK_ENV') == 'development'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))

    print(f"Starting BarSan Backend on {host}:{port}")
    print(f"Debug mode: {debug}")

    app.run(debug=debug, host=host, port=port)
