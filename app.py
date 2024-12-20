from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, login_manager
from datetime import datetime
import os

app = Flask(__name__)

# Configure the base directory for SQLite and secret key for sessions
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize the LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize SQLAlchemy without a specific URI, as it will be set dynamically per user
db = SQLAlchemy(app)

# User model for authentication
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

# User loader function for Flask-Login
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
        if user and user.password == password:  # Simple check, use hashed passwords in production
            login_user(user)
            # Set user-specific database URI dynamically
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///users/{username}_notes.db"
            with app.app_context():
                db.create_all()  # Create tables in the user's database
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
    app.run()
                
