from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(__name__)

# Configure the application
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Default database URI (used before user login)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default.db'

# Initialize the database
db = SQLAlchemy(app)

# Initialize the login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Note model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), nullable=True)
    reminder = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route to login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # In production, use hashed passwords
            login_user(user)
            # Set user-specific database URI
            user_db_uri = f"sqlite:///users/{username}_notes.db"
            app.config['SQLALCHEMY_DATABASE_URI'] = user_db_uri
            
            # Create all tables for this user
            with app.app_context():
                db.create_all()
            
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

# Route to log out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route for the home page
@app.route('/')
@login_required
def home():
    query = request.args.get('search', '')
    if query:
        notes = Note.query.filter(Note.title.ilike(f"%{query}%")).all()
    else:
        notes = Note.query.all()
    no_notes = len(notes) == 0
    return render_template('home.html', notes=notes, no_notes=no_notes, query=query)

# Route to display the create note form
@app.route('/create-note')
@login_required
def create_note_form():
    return render_template('index.html')

# Route to create a new note
@app.route('/notes', methods=['POST'])
@login_required
def create_note():
    data = request.json
    reminder = datetime.fromisoformat(data.get('reminder')) if data.get('reminder') else None

    new_note = Note(
        title=data['title'],
        content=data['content'],
        tags=data.get('tags', ''),
        reminder=reminder,
        user_id=current_user.id
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully'}), 201

# Route to delete a note by its ID
@app.route('/notes/<int:id>', methods=['DELETE'])
@login_required
def delete_note(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return '', 204

# Route to render the edit note form
@app.route('/notes/<int:id>/edit', methods=['GET'])
@login_required
def edit_note_form(id):
    note = Note.query.get_or_404(id)
    return render_template('edit.html', note=note)

# Route to update a note
@app.route('/notes/<int:id>', methods=['PUT'])
@login_required
def update_note(id):
    note = Note.query.get_or_404(id)
    data = request.json
    note.title = data['title']
    note.content = data['content']
    note.tags = data.get('tags', '')
    note.reminder = datetime.fromisoformat(data['reminder']) if data.get('reminder') else None
    db.session.commit()
    return jsonify({'message': 'Note updated successfully'}), 200

# Route to register a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('User registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    # Ensure the 'users' directory exists for storing user databases
    if not os.path.exists('users'):
        os.makedirs('users')
    
    # Initialize the default database
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
