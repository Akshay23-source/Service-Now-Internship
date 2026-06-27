from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    """
    Callback function used by Flask-Login to load a user object 
    from the user ID stored in the session cookie.
    """
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    """
    User model representing registered users.
    Inherits from:
      - db.Model: Integrates the class with SQLAlchemy ORM.
      - UserMixin: Provides default implementations for properties 
        (is_authenticated, is_active, is_anonymous, get_id) that Flask-Login expects.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship linking users to their notes.
    # lazy='dynamic' returns a query object, enabling sorting/filtering on notes queries.
    notes = db.relationship('Note', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashes the input password and stores the resulting hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Note(db.Model):
    """
    Note model representing a markdown or rich text smart note.
    Linked to a specific User via a foreign key user_id.
    """
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Establish foreign key constraint mapping back to users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # 1-to-1 Relationship mapping to generated AI quiz.
    # uselist=False ensures the relationship acts as a direct object lookup (note.quiz yields a single Quiz or None).
    quiz = db.relationship('Quiz', backref='note', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Note {self.title}>'


class Quiz(db.Model):
    """
    Quiz model representing multiple choice testing questions generated off a Note.
    Linked as 1-to-1 relationship with the parent Note.
    """
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    
    # Store questions list serialized as raw JSON text
    questions_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ForeignKey relation pointing to notes table, unique=True enforces 1-to-1 constraint
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id', ondelete='CASCADE'), unique=True, nullable=False)

    def __repr__(self):
        return f'<Quiz for Note #{self.note_id}>'

