from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.template_folder = 'login'

# Ensure the instance directory exists
os.makedirs(app.instance_path, exist_ok=True)

# Initialize Flask extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the User model
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    role = db.Column(db.String(10), nullable=False, default='user')

    def __repr__(self):
        return f'<User {self.username}>'

# Define the Data model
class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Data {self.order_id}>'

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please provide both username and password', 'danger')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('user_page'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')
        gender = request.form.get('gender')
        role = request.form.get('role', 'user')
        if not username or not password:
            flash('Please provide both username and password', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, phone_number=phone_number, gender=gender, role=role)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully!', 'success')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: user.phone_number' in str(e):
                flash('Error: Phone number already exists. Please use a different phone number.', 'danger')
            else:
                flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/user_page', methods=['GET', 'POST'])
@login_required
def user_page():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        category = request.form.get('category')
        date = request.form.get('date')
        status = request.form.get('status')
        new_data = Data(user_id=current_user.id, order_id=order_id, category=category, date=date, status=status)
        try:
            db.session.add(new_data)
            db.session.commit()
            flash('Data added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    data_entries = Data.query.filter_by(user_id=current_user.id).all()
    return render_template('userPage.html', user=current_user, data_entries=data_entries)

@app.route('/admin_page', methods=['GET', 'POST'])
@login_required
def admin_page():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('user_page'))
    users = User.query.all()
    if request.method == 'POST':
        username = request.form.get('username')
        phone_number = request.form.get('phone_number')
        if username and phone_number:
            hashed_password = generate_password_hash('defaultpassword', method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password, phone_number=phone_number)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('User added successfully!', 'success')
            except IntegrityError as e:
                db.session.rollback()
                if 'UNIQUE constraint failed: user.phone_number' in str(e):
                    flash('Error: Phone number already exists. Please use a different phone number.', 'danger')
                else:
                    flash('An error occurred. Please try again.', 'danger')
    if request.method == 'POST' and request.form.get('delete_user'):
        user_id = request.form.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                try:
                    db.session.delete(user)
                    db.session.commit()
                    flash(f'User {user.username} deleted successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error deleting user: {str(e)}', 'danger')
    return render_template('adminpage.html', user=current_user, users=users)

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('user_page'))
    username = request.form.get('username')
    phone_number = request.form.get('phone_number')
    if username and phone_number:
        hashed_password = generate_password_hash('defaultpassword', method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, phone_number=phone_number)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: user.phone_number' in str(e):
                flash('Error: Phone number already exists. Please use a different phone number.', 'danger')
            else:
                flash('An error occurred. Please try again.', 'danger')
    return redirect(url_for('admin_page'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)
