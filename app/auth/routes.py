from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlsplit
from app import db
from app.auth import auth_bp
from app.auth.forms import SignupForm, LoginForm
from app.models import User

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Renders signup form. If POST is valid, hashes user's password,
    persists them in the database, and redirects them to the login page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = SignupForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.strip().lower())
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/signup.html', title='Sign Up', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders login form. If POST is valid, verifies user exists and 
    password hashes match. Establishes session and handles safe redirecting.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        
        # Security validation to prevent Open Redirect Vulnerability:
        # If 'next' contains a full domain (e.g. http://attacker.com),
        # urlsplit(next_page).netloc will not be empty. We redirect only if netloc is empty.
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.dashboard')
            
        flash(f'Logged in successfully as {user.email}!', 'success')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Logs out the current user, terminates their session, and redirects to login.
    """
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

