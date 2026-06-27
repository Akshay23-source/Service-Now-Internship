from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class SignupForm(FlaskForm):
    """
    Form for registering a new user.
    Performs validation on email and password matches.
    """
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.'),
            Length(max=120, message='Email is too long.')
        ]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, message='Password must be at least 8 characters long.')
        ]
    )
    
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        """
        Custom validator for the email field.
        WTForms automatically calls any method starting with 'validate_' followed by field name.
        """
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError('Email is already registered. Please log in or use a different one.')


class LoginForm(FlaskForm):
    """
    Form for logging in an existing user.
    """
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.')
        ]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.')
        ]
    )
    
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
