import os
import uuid
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import time
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')
# 500 MB max upload size
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rooted.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cloudinary Setup
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Authlib OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    handle = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(250), default='')
    profile_photo_url = db.Column(db.String(200), default='')
    account_tier = db.Column(db.String(20), default='Free')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Post(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    sender = db.Column(db.String(100))
    handle = db.Column(db.String(50))
    text = db.Column(db.String(500))
    media_url = db.Column(db.String(200))
    media_type = db.Column(db.String(20))
    timestamp = db.Column(db.Integer)
    likes = db.Column(db.Integer, default=0)
    bookmarks = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    node = db.Column(db.String(50), default='For You')
    parent_id = db.Column(db.String(50), db.ForeignKey('post.id'), nullable=True)
    is_retweet = db.Column(db.Boolean, default=False)
    original_post_id = db.Column(db.String(50), db.ForeignKey('post.id'), nullable=True)

with app.app_context():
    db.create_all()

# Enable SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=500*1024*1024)

@app.route('/')
def index():
    user_data = None
    if current_user.is_authenticated:
        user_data = {
            'name': current_user.display_name,
            'handle': current_user.handle,
            'uuid': current_user.uuid,
            'photo': current_user.profile_photo_url,
            'bio': current_user.bio
        }
    return render_template('index.html', current_user=user_data)

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('auth_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorized')
def auth_google():
    token = google.authorize_access_token()
    # With OpenID Connect, userinfo is parsed directly into the token
    user_info = token.get('userinfo')
    if not user_info:
        user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    
    email = user_info['email']
    display_name = user_info.get('name', email.split('@')[0])
    
    user = User.query.filter_by(email=email).first()
    if not user:
        base_handle = "@" + display_name.lower().replace(" ", "")
        handle = base_handle
        counter = 1
        while User.query.filter_by(handle=handle).first():
            handle = f"{base_handle}{counter}"
            counter += 1
            
        user = User(
            email=email,
            display_name=display_name,
            handle=handle,
            profile_photo_url=user_info.get('picture', '')
        )
        db.session.add(user)
        db.session.commit()
        
    login_user(user)
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'media' not in request.files:
        return jsonify({'error': 'No media part'}), 400
    file = request.files['media']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    upload_type = request.form.get('type', 'post')
    
    try:
        if file.mimetype.startswith('video/'):
            upload_result = cloudinary.uploader.upload(file, resource_type="video")
            media_type = 'video'
        else:
            upload_result = cloudinary.uploader.upload(file)
            media_type = 'image'
            
        url = upload_result.get('secure_url')
        
        if upload_type == 'profile':
            current_user.profile_photo_url = url
            db.session.commit()
            return jsonify({'success': True, 'url': url, 'type': media_type, 'profile_updated': True})
            
        return jsonify({'success': True, 'url': url, 'type': media_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('join')
def handle_join(user_data):
    # Fetch top 200 recent posts
    recent_posts = Post.query.order_by(Post.timestamp.desc()).limit(200).all()
    
    def get_score(p):
        score = p.likes + (p.bookmarks * 10) + (p.reply_count * 150)
        # Add a tiny bit of recency bias so new posts aren't always strictly at 0 below old 0s
        score += (p.timestamp / 1000000000000.0) 
        user = User.query.filter_by(handle=p.handle).first()
        if user and user.account_tier == 'Premium+':
            score *= 10
        return score
        
    # Sort algorithmically
    recent_posts.sort(key=get_score, reverse=True)
    # Send top 100
    for p in recent_posts[:100]:
        reply_to_handle = None
        if p.parent_id:
            parent_post = Post.query.get(p.parent_id)
            if parent_post:
                reply_to_handle = parent_post.handle
                
        retweeted_from = None
        if p.is_retweet and p.original_post_id:
            orig = Post.query.get(p.original_post_id)
            if orig:
                retweeted_from = orig.handle
                
        post_data = {
            'id': p.id,
            'sender': p.sender,
            'handle': p.handle,
            'text': p.text,
            'mediaUrl': p.media_url,
            'mediaType': p.media_type,
            'timestamp': p.timestamp,
            'likes': p.likes,
            'bookmarks': p.bookmarks,
            'node': p.node,
            'parentId': p.parent_id,
            'replyToHandle': reply_to_handle,
            'isRetweet': p.is_retweet,
            'originalPostId': p.original_post_id,
            'retweetedFrom': retweeted_from
        }
        emit('receive_post', post_data)

@socketio.on('create_post')
def handle_create_post(data):
    post_id = str(int(time.time() * 1000))
    handle = data.get('handle', '@user')
    sender = data.get('sender', 'Anonymous')
    
    parent_id = data.get('parentId')
    if parent_id:
        parent_post = Post.query.get(parent_id)
        if parent_post:
            parent_post.reply_count += 1
            db.session.commit()
            
    post = Post(
        id=post_id,
        sender=sender,
        handle=handle,
        text=data.get('text', ''),
        media_url=data.get('mediaUrl'),
        media_type=data.get('mediaType'),
        timestamp=int(time.time() * 1000),
        likes=0,
        bookmarks=0,
        reply_count=0,
        node=data.get('node', 'For You'),
        parent_id=parent_id,
        is_retweet=data.get('isRetweet', False),
        original_post_id=data.get('originalPostId')
    )
    db.session.add(post)
    db.session.commit()
    
    reply_to_handle = None
    if post.parent_id:
        parent_post = Post.query.get(post.parent_id)
        if parent_post:
            reply_to_handle = parent_post.handle
            
    retweeted_from = None
    if post.is_retweet and post.original_post_id:
        orig = Post.query.get(post.original_post_id)
        if orig:
            retweeted_from = orig.handle
            
    post_data = {
        'id': post.id,
        'sender': post.sender,
        'handle': post.handle,
        'text': post.text,
        'mediaUrl': post.media_url,
        'mediaType': post.media_type,
        'timestamp': post.timestamp,
        'likes': post.likes,
        'bookmarks': post.bookmarks,
        'node': post.node,
        'parentId': post.parent_id,
        'replyToHandle': reply_to_handle,
        'isRetweet': post.is_retweet,
        'originalPostId': post.original_post_id,
        'retweetedFrom': retweeted_from
    }
    emit('receive_post', post_data, broadcast=True)

@socketio.on('bookmark_post')
def handle_bookmark_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post.bookmarks += 1
        db.session.commit()

@socketio.on('like_post')
def handle_like_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post.likes += 1
        db.session.commit()
        emit('update_likes', {'id': post_id, 'likes': post.likes}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

