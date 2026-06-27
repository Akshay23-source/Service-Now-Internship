from flask import Blueprint

# Initialize the main blueprint which hosts key user dashboards and landing route redirects.
main_bp = Blueprint('main', __name__)

from app.main import routes
