from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from database import db
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)

bcrypt = Bcrypt(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from models import User, Classroom, Photo, Game

# login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
# context processor for user_id 
# for displaying of the username in place of the login button
@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    if user_id:
        user = db.session.get(User, user_id)
        return dict(current_user=user)
    return dict(current_user=None)

# routes
@app.route('/')
def start():
    return render_template('start.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        next_page = request.args.get('next', '/')
        if action == 'login':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and user.password and bcrypt.check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(next_page)
            return render_template('login.html', error='Invalid credentials')
        elif action == 'signup':
            username = request.form['username']
            password = request.form['password']
            if User.query.filter_by(username=username).first():
                return render_template('login.html', error='Username already exists')
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, password=hashed)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return redirect(next_page)
        elif action == 'guest':
            guestname = request.form['guestname']
            if User.query.filter_by(username=guestname).first():
                return render_template('login.html', error='Guestname taken')
            user = User(username=guestname, is_guest=True)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return redirect(next_page)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None) 
    return redirect(url_for('start'))

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

@app.route('/leaderboard')
def leaderboard():
    main = User.query.order_by(User.total_score.desc()).limit(10).all()
    contrib = db.session.query(User.username, db.func.count(Photo.id).label('contributions'))\
        .join(Photo, User.id == Photo.uploaded_by)\
        .filter(Photo.is_approved == True)\
        .group_by(User.id)\
        .order_by(db.func.count(Photo.id).desc())\
        .limit(10).all()
    return render_template('leaderboard.html', main=main, contrib=contrib)

@app.route('/contribute', methods=['GET', 'POST'])
@login_required
def contribute():
    if request.method == 'POST':
        classroom_id = request.form.get('classroom_id')
        file = request.files.get('image')
        
        # checking if required fields are present
        if not file:
            return render_template('contribute.html', error='Please upload an image')
        if not classroom_id:
            return render_template('contribute.html', error='Please select a classroom')
        
        # validating and processing the submission
        try:
            classroom_id = int(classroom_id)
            classroom = db.session.get(Classroom, classroom_id)
            if not classroom:
                return render_template('contribute.html', error='Invalid classroom selected')
            
            # save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # create and save the photo record
            photo = Photo(classroom_id=classroom_id, uploaded_by=session['user_id'], image_url=file_path)
            db.session.add(photo)
            db.session.commit()
            
            return render_template('contribute.html', message='Thank you for contributing!')
        except ValueError:
            return render_template('contribute.html', error='Invalid classroom ID')
        except Exception as e:
            print(f"Error saving photo: {e}")
            return render_template('contribute.html', error='An error occurred while saving your contribution')
    
    return render_template('contribute.html')

# API Routes
@app.route('/api/get_photos')
@login_required
def get_photos():
    photos = Photo.query.filter_by(is_approved=True).order_by(db.func.random()).limit(5).all()
    return jsonify([{'id': p.id, 'image_url': p.image_url} for p in photos])

@app.route('/api/guess', methods=['POST'])
@login_required
def guess():
    data = request.json
    photo = db.session.get(Photo, data['photo_id'])
    classroom = db.session.get(Classroom, photo.classroom_id)
    guess = {'building': data['building'], 'floor': data['floor'], 'classroom': data['classroom']}
    correct = {'building': classroom.building, 'floor': classroom.floor, 'classroom': classroom.classroom_number}
    
    if guess['classroom'] == correct['classroom']:
        score = 5
    elif guess['building'] == correct['building'] and int(guess['floor']) == correct['floor']:
        score = 3
    elif int(guess['floor']) == correct['floor']:
        score = 2
    elif guess['building'] == correct['building']:
        score = 1
    else:
        score = 0
    
    feedback = {
        'score': score,
        'correct': score == 5,
        'correct_building': correct['building'] if score < 5 else None,
        'correct_floor': correct['floor'] if score < 5 else None,
        'correct_classroom': correct['classroom'] if score < 5 else None
    }
    return jsonify(feedback)

@app.route('/api/save_score', methods=['POST'])
@login_required
def save_score():
    data = request.json
    score = data['score']
    user = db.session.get(User, session['user_id'])
    game = Game(user_id=user.id, score=score)
    user.total_score += score
    if score > user.high_score:
        user.high_score = score
    db.session.add(game)
    db.session.commit()
    return jsonify({'high_score': user.high_score})

@app.route('/api/classrooms')
def get_classrooms():
    building = request.args.get('building')
    floor = request.args.get('floor')
    filter_text = request.args.get('filter', '')
    query = Classroom.query
    if building:
        query = query.filter_by(building=building)
    if floor and floor.strip():  # check if floor is non-empty
        try:
            query = query.filter_by(floor=int(floor))
        except ValueError:
            return jsonify({'error': 'Invalid floor value'}), 400
    if filter_text:
        query = query.filter(Classroom.classroom_number.like(f'%{filter_text}%'))
    classrooms = query.all()
    return jsonify([{'id': c.id, 'classroom_number': c.classroom_number} for c in classrooms])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # create tables if they don't exist
    app.run(debug=True)