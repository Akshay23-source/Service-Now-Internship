import os
from app import create_app, db
from app.models import User

app = create_app()

# Create tables in SQLite database if they don't exist.
# We must execute database creation within Flask's 'app_context'.
# Why? Flask-SQLAlchemy needs to read the app's configuration (like database URI) 
# which is only accessible when an active application context is running.
with app.app_context():
    # Ensure the 'instance' folder exists (SQLite DB file resides here)
    os.makedirs(app.instance_path, exist_ok=True)
    db.create_all()
    print("Database tables initialized successfully.")

if __name__ == '__main__':
    # Start the local development server
    # host='0.0.0.0' allows external access (e.g. testing from mobile or subagent browser)
    # debug=True enables auto-reloading and helpful interactive stack traces in browser
    app.run(debug=True, host='0.0.0.0', port=5000)
