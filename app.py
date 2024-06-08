from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Optional: Auto-reload templates in development
app.template_folder = 'login'  # Set the custom template folder
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20))  # Assuming phone number is a string
    gender = db.Column(db.String(10))  # Assuming gender is a string, can be 'male', 'female', 'other'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please provide both username and password')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')
        gender = request.form.get('gender')
        if not username or not password:
            flash('Please provide both username and password')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password, phone_number=phone_number, gender=gender)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return 'Welcome to your dashboard!'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
