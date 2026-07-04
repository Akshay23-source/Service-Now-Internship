from app import create_app, db

app = create_app()

# Initialize SQLite database tables on Vercel boot inside the app context
with app.app_context():
    import os
    if os.environ.get('VERCEL') == '1':
        db.create_all()

if __name__ == "__main__":
    app.run()
