from flask import Blueprint

# Define the 'auth' blueprint. This allows us to modularize authentication routes 
# and prefix them all (e.g. /auth/login, /auth/signup) in a clean directory structure.
auth_bp = Blueprint('auth', __name__)

# Import routes at the bottom of the file to prevent circular imports 
# (since routes will also need to import auth_bp)
from app.auth import routes
