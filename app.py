from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from googletrans import Translator
from datetime import datetime
from forms import RegistrationForm, LoginForm
from models import User, Message, db
import eventlet
import re

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, async_mode='eventlet')

translator = Translator()

# dictionaries for each language
idioms = {
    'en': {
        "break a leg": "Good luck",
        "piece of cake": "Very easy",
        "hit the sack": "Go to bed",
    },
    'es': {
        "tirar la toalla": "Give up",
        "estar en las nubes": "Daydreaming",
        "dormir como un tronco": "Sleep like a log",
    },
    'fr': {
        "poser un lapin": "Stand someone up",
        "coûter les yeux de la tête": "Cost an arm and a leg",
        "avoir un chat dans la gorge": "Have a frog in one's throat",
    },
    'de': {
        "den Nagel auf den Kopf treffen": "Hit the nail on the head",
        "ins Gras beißen": "Kick the bucket",
        "die Daumen drücken": "Keep one's fingers crossed",
    },
    'zh-cn': {
        "杯弓蛇影": "Overreact due to imaginary fears",
        "画蛇添足": "To overdo it",
        "盲人摸象": "To draw conclusions from incomplete data",
    }
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('chat'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/chat')
@login_required
def chat():
    users = User.query.all()
    return render_template('chat.html', title='Chat', users=users)

@app.route('/messages', methods=['GET'])
@login_required
def get_messages():
    recipient_id = request.args.get('recipient_id')
    if recipient_id:
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient_id)) |
            ((Message.sender_id == recipient_id) & (Message.recipient_id == current_user.id))
        ).order_by(Message.timestamp.asc()).all()
    else:
        messages = []
    return jsonify([{
            'content': msg.content,
            'timestamp': msg.timestamp,
            'author': msg.author.username,
            'recipient': msg.recipient.username,
            'sender_id': msg.sender_id,
            'idioms': find_idioms(msg.content, 'en')  # Assuming 'en' as default
        } for msg in messages])

@app.route('/translate', methods=['POST'])
@login_required
def translate_message():
    data = request.get_json()
    text = data.get('text')
    dest_lang = data.get('dest_lang')
    translated = translator.translate(text, dest=dest_lang)
    return jsonify({'translated_text': translated.text})

@app.route('/search_users', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('query')
    users = User.query.filter(User.username.like(f"%{query}%")).all()
    return jsonify([{'id': user.id, 'username': user.username} for user in users])

@app.route('/users', methods=['GET'])
@login_required
def get_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username} for user in users])

# @socketio.on('message')
# @login_required
# def handleMessage(data):
#     recipient = User.query.filter_by(username=data['recipient']).first()
#     if recipient:
#         message = Message(content=data['message'], author=current_user, recipient=recipient)
#         db.session.add(message)
#         db.session.commit()
#         emit('message', {
#             'message': data['message'],
#             'author': current_user.username,
#             'recipient': recipient.username,
#             'sender_id': current_user.id,
#             'idioms': find_idioms(data['message'], data.get('lang', 'en'))  # Check for idioms in the specified language
#         }, broadcast=True)
@socketio.on('message')
@login_required
def handleMessage(data):
    recipient = User.query.filter_by(username=data['recipient']).first()
    if recipient:
        message = Message(content=data['message'], author=current_user, recipient=recipient)
        db.session.add(message)
        db.session.commit()
        idioms_found = find_idioms(data['message'], data.get('lang', 'en'))  # Find idioms and their meanings
        emit('message', {
            'message': data['message'],
            'author': current_user.username,
            'recipient': recipient.username,
            'sender_id': current_user.id,
            'idioms': idioms_found  # Send the idiom meanings
        }, broadcast=True)


def find_idioms(text, lang):
    found_idioms = []
    for idiom, meaning in idioms.get(lang, {}).items():
        if re.search(r'\b' + re.escape(idiom) + r'\b', text):
            found_idioms.append({'meaning': meaning})
    return found_idioms

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
