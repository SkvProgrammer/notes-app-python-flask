from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Note model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), nullable=True)
    reminder = db.Column(db.DateTime, nullable=True)

# Initialize the database
with app.app_context():
    db.create_all()

# Route for the home page
@app.route('/')
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
def create_note_form():
    return render_template('index.html')

# Route to create a new note
@app.route('/notes', methods=['POST'])
def create_note():
    data = request.json
    reminder = datetime.fromisoformat(data.get('reminder')) if data.get('reminder') else None

    new_note = Note(
        title=data['title'],
        content=data['content'],
        tags=data.get('tags', ''),
        reminder=reminder
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully'}), 201

# Route to delete a note by its ID
@app.route('/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return '', 204

# Route to render the edit note form
@app.route('/notes/<int:id>/edit', methods=['GET'])
def edit_note_form(id):
    note = Note.query.get_or_404(id)
    return render_template('edit.html', note=note)

# Route to update a note
@app.route('/notes/<int:id>', methods=['PUT'])
def update_note(id):
    note = Note.query.get_or_404(id)
    data = request.json
    note.title = data['title']
    note.content = data['content']
    note.tags = data.get('tags', '')
    note.reminder = datetime.fromisoformat(data['reminder']) if data.get('reminder') else None
    db.session.commit()
    return jsonify({'message': 'Note updated successfully'}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Railway sets PORT in environment variables
    app.run(host="0.0.0.0", port=port)
    
