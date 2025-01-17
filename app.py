import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests

# Initialize Flask app and logging
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospitalmap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure logging to display logs in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    hospital_data = db.Column(db.Text, nullable=False)  # JSON string to store hospital list

# Login manager loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ensure tables are created before any request
tables_initialized = False

@app.before_request
def create_tables_once():
    global tables_initialized
    if not tables_initialized:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created or already exist.")
        tables_initialized = True

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Log user input
        logger.info(f"Signup attempt with username: {username}, email: {email}")

        # Check if the email already exists
        if User.query.filter_by(email=email).first():
            logger.warning(f"Signup failed: Email {email} already exists.")
            flash('Email already exists', 'danger')
            return redirect(url_for('signup'))

        try:
            # Hash the password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=hashed_password)

            # Add the user to the database
            db.session.add(new_user)
            db.session.commit()

            logger.info(f"User {username} successfully signed up with email {email}.")
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during signup for email {email}: {str(e)}")
            flash('An error occurred while creating your account. Please try again later.', 'danger')
            return redirect(url_for('signup'))

    logger.info("Rendering signup page.")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        logger.info(f"User {user.username} logged in successfully.")
        return redirect(url_for('search'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"User {current_user.username} logged out.")
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/search', methods=['GET'])
@login_required
def search():
    return render_template('search.html', username=current_user.username)

@app.route('/api/search_hospitals', methods=['POST'])
@login_required
def search_hospitals():
    data = request.json
    user_lat = data.get('latitude')
    user_lng = data.get('longitude')

    if not user_lat or not user_lng:
        logger.error("Latitude or Longitude not provided in the request.")
        return jsonify({'error': 'Latitude and Longitude are required'}), 400

    logger.info(f"Searching hospitals near ({user_lat}, {user_lng}) for user {current_user.username}.")

    # HERE Maps Places API request
    api_url = "https://discover.search.hereapi.com/v1/discover"
    params = {
        'apikey': 'AnNqHPQq1CjIAlhwXf7m0OiN54e8hOD43y7u0v1dYuY',
        'q': 'hospital',
        'at': f'{user_lat},{user_lng}',
        'limit': 4
    }
    response = requests.get(api_url, params=params)

    if response.status_code != 200:
        logger.error(f"Error fetching data from HERE Maps API: {response.text}")
        return jsonify({'error': 'Error fetching data from HERE Maps API'}), 500

    hospital_data = response.json().get('items', [])
    logger.info(f"Found {len(hospital_data)} hospitals near the user.")

    # Save location and hospitals to database
    location = Location(
        user_id=current_user.id,
        latitude=user_lat,
        longitude=user_lng,
        hospital_data=str(hospital_data)
    )
    db.session.add(location)
    db.session.commit()

    return jsonify(hospital_data)

@app.route('/api/get_hospitals', methods=['GET'])
@login_required
def get_hospitals():
    user_locations = Location.query.filter_by(user_id=current_user.id).all()
    if not user_locations:
        logger.warning(f"No locations found for user {current_user.username}.")
        return jsonify([])

    data = [
        {
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'hospitals': eval(loc.hospital_data)
        }
        for loc in user_locations
    ]
    return jsonify(data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
