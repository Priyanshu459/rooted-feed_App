import gevent.monkey
gevent.monkey.patch_all()

import os
import uuid
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, url_for, redirect
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import time
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
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

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

follow_requests = db.Table('follow_requests',
    db.Column('requester_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('requested_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    handle = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(250), default='')
    profile_photo_url = db.Column(db.String(200), default='')
    account_tier = db.Column(db.String(20), default='Free')
    is_private = db.Column(db.Boolean, default=False)
    
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
        
    requests_sent = db.relationship(
        'User', secondary=follow_requests,
        primaryjoin=(follow_requests.c.requester_id == id),
        secondaryjoin=(follow_requests.c.requested_id == id),
        backref=db.backref('requests_received', lazy='dynamic'), lazy='dynamic')
        
    def is_following(self, user):
        return self.followed.filter_by(id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Conversation(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.Integer)
    messages = db.relationship('Message', backref='conversation', lazy='dynamic')

class Message(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversation.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text = db.Column(db.String(1000))
    timestamp = db.Column(db.Integer)
    read = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Owner
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Triggers it
    type = db.Column(db.String(50), nullable=False) # follow, follow_request, like, retweet, message
    content = db.Column(db.String(250))
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.Integer)
    
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    def to_dict(self):
        sender_handle = self.sender.handle if self.sender else None
        sender_name = self.sender.display_name if self.sender else None
        sender_photo = self.sender.profile_photo_url if self.sender else None
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'is_read': self.is_read,
            'timestamp': self.timestamp,
            'sender_handle': sender_handle,
            'sender_name': sender_name,
            'sender_photo': sender_photo
        }

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

class PostLike(db.Model):
    """Tracks which user liked which post — enforces one like per user per post."""
    __tablename__ = 'post_like'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    post_id = db.Column(db.String(50), db.ForeignKey('post.id'), primary_key=True)

with app.app_context():
    db.create_all()

# Enable SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=500*1024*1024)

@app.route('/')
def index():
    user_data = None
    if current_user.is_authenticated:
        user_data = {
            'id': current_user.id,
            'name': current_user.display_name,
            'handle': current_user.handle,
            'uuid': current_user.uuid,
            'photo': current_user.profile_photo_url,
            'bio': current_user.bio,
            'is_private': current_user.is_private
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
    upload_type = request.form.get('type', 'post')
    url = None
    media_type = None
    
    if 'media' in request.files and request.files['media'].filename != '':
        file = request.files['media']
        try:
            if file.mimetype.startswith('video/'):
                upload_result = cloudinary.uploader.upload(file, resource_type="video")
                media_type = 'video'
            else:
                upload_result = cloudinary.uploader.upload(file)
                media_type = 'image'
            url = upload_result.get('secure_url')
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif upload_type != 'profile':
        return jsonify({'error': 'No media part'}), 400
        
    try:
        if upload_type == 'profile':
            new_name = request.form.get('name')
            new_bio = request.form.get('bio')
            is_private = request.form.get('is_private') == 'true'
            
            if url:
                current_user.profile_photo_url = url
            if new_name:
                current_user.display_name = new_name
            if new_bio is not None:
                current_user.bio = new_bio
            current_user.is_private = is_private
                
            db.session.commit()
            return jsonify({'success': True, 'url': url, 'type': media_type, 'profile_updated': True})
            
        return jsonify({'success': True, 'url': url, 'type': media_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<handle>')
def get_user_profile(handle):
    user = User.query.filter_by(handle=handle).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    is_following = False
    is_mutual = False
    is_requested = False
    if current_user.is_authenticated:
        is_following = current_user.is_following(user)
        is_mutual = is_following and user.is_following(current_user)
        is_requested = user in current_user.requests_sent
        
    return jsonify({
        'handle': user.handle,
        'name': user.display_name,
        'bio': user.bio,
        'photo': user.profile_photo_url,
        'followers_count': user.followers.count(),
        'following_count': user.followed.count(),
        'is_following': is_following,
        'is_mutual': is_mutual,
        'is_requested': is_requested,
        'is_self': current_user.is_authenticated and current_user.id == user.id
    })

def post_to_dict(p, viewer_id=None):
    user = User.query.filter_by(handle=p.handle).first()
    sender_name = user.display_name if user else p.sender
    sender_photo = user.profile_photo_url if user else None
    
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

    # Check if the current viewer has already liked this post
    user_liked = False
    if viewer_id:
        user_liked = PostLike.query.filter_by(user_id=viewer_id, post_id=p.id).first() is not None
            
    return {
        'id': p.id,
        'sender': sender_name,
        'senderPhoto': sender_photo,
        'handle': p.handle,
        'text': p.text,
        'mediaUrl': p.media_url,
        'mediaType': p.media_type,
        'timestamp': p.timestamp,
        'likes': p.likes,
        'bookmarks': p.bookmarks,
        'replyCount': getattr(p, 'reply_count', 0),
        'node': p.node,
        'parentId': p.parent_id,
        'replyToHandle': reply_to_handle,
        'isRetweet': p.is_retweet,
        'originalPostId': p.original_post_id,
        'retweetedFrom': retweeted_from,
        'userLiked': user_liked
    }

@app.route('/api/posts/following')
@login_required
def get_following_posts():
    followed_ids = [u.id for u in current_user.followed]
    # Include own posts too
    followed_ids.append(current_user.id)
    
    posts = Post.query.filter(Post.sender.in_([User.query.get(i).handle for i in followed_ids])).order_by(Post.timestamp.desc()).limit(100).all()
    
    viewer_id = current_user.id if current_user.is_authenticated else None
    res = [post_to_dict(p, viewer_id) for p in posts]
    return jsonify(res)

@app.route('/api/follow/<handle>', methods=['POST'])
@login_required
def follow_user(handle):
    user = User.query.filter_by(handle=handle).first()
    if not user or user == current_user:
        return jsonify({'error': 'Invalid action'}), 400
        
    ts = int(time.time() * 1000)
    
    if user.is_private:
        # Check if request already sent
        existing = Notification.query.filter_by(user_id=user.id, sender_id=current_user.id, type='follow_request').first()
        if not existing:
            current_user.requests_sent.append(user)
            n = Notification(user_id=user.id, sender_id=current_user.id, type='follow_request', content=f"{current_user.display_name} requested to follow you.", timestamp=ts)
            db.session.add(n)
            socketio.emit('receive_notification', n.to_dict(), room=f"user_{user.id}")
            db.session.commit()
        return jsonify({'success': True, 'status': 'requested'})
    else:
        current_user.follow(user)
        n = Notification(user_id=user.id, sender_id=current_user.id, type='follow', content=f"{current_user.display_name} started following you.", timestamp=ts)
        db.session.add(n)
        socketio.emit('receive_notification', n.to_dict(), room=f"user_{user.id}")
        db.session.commit()
        return jsonify({'success': True, 'status': 'following'})

@app.route('/api/unfollow/<handle>', methods=['POST'])
@login_required
def unfollow_user(handle):
    user = User.query.filter_by(handle=handle).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Remove from requests if pending
    if user in current_user.requests_sent:
        current_user.requests_sent.remove(user)
        n = Notification.query.filter_by(user_id=user.id, sender_id=current_user.id, type='follow_request').first()
        if n: db.session.delete(n)
        
    current_user.unfollow(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/follow/accept/<handle>', methods=['POST'])
@login_required
def accept_follow(handle):
    sender = User.query.filter_by(handle=handle).first()
    if not sender or current_user not in sender.requests_sent:
        return jsonify({'error': 'Invalid request'}), 400
        
    sender.requests_sent.remove(current_user)
    sender.follow(current_user)
    
    # Mark notification as read/handled
    n = Notification.query.filter_by(user_id=current_user.id, sender_id=sender.id, type='follow_request').first()
    if n:
        n.type = 'follow'
        n.content = f"{sender.display_name} started following you."
        n.is_read = True
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/follow/decline/<handle>', methods=['POST'])
@login_required
def decline_follow(handle):
    sender = User.query.filter_by(handle=handle).first()
    if sender and current_user in sender.requests_sent:
        sender.requests_sent.remove(current_user)
        n = Notification.query.filter_by(user_id=current_user.id, sender_id=sender.id, type='follow_request').first()
        if n: db.session.delete(n)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/notifications')
@login_required
def get_notifications():
    notifs = current_user.notifications.order_by(Notification.timestamp.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notifs])

@app.route('/api/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    unread = current_user.notifications.filter_by(is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/conversations')
@login_required
def get_conversations():
    convs = Conversation.query.filter(
        (Conversation.user1_id == current_user.id) | (Conversation.user2_id == current_user.id)
    ).order_by(Conversation.updated_at.desc()).all()
    res = []
    for c in convs:
        other_user = User.query.get(c.user2_id if c.user1_id == current_user.id else c.user1_id)
        last_msg = c.messages.order_by(Message.timestamp.desc()).first()
        unread_count = c.messages.filter_by(read=False).filter(Message.sender_id != current_user.id).count()
        if last_msg:
            res.append({
                'id': c.id,
                'other_user': {'handle': other_user.handle, 'name': other_user.display_name, 'photo': other_user.profile_photo_url},
                'last_message': last_msg.text,
                'timestamp': last_msg.timestamp,
                'unread_count': unread_count
            })
    return jsonify(res)

@app.route('/api/messages/<handle>')
@login_required
def get_messages(handle):
    other_user = User.query.filter_by(handle=handle).first()
    if not other_user: return jsonify({'error': 'Not found'}), 404
    conv = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == other_user.id)) |
        ((Conversation.user1_id == other_user.id) & (Conversation.user2_id == current_user.id))
    ).first()
    if not conv: return jsonify([])
    
    unread = conv.messages.filter_by(read=False).filter(Message.sender_id != current_user.id).all()
    for m in unread: m.read = True
    if unread: db.session.commit()
    
    messages = conv.messages.order_by(Message.timestamp.asc()).all()
    return jsonify([{
        'id': m.id, 'sender_id': m.sender_id, 'text': m.text, 'timestamp': m.timestamp, 'is_me': m.sender_id == current_user.id
    } for m in messages])

from flask_socketio import join_room

@socketio.on('join_chat')
def join_chat(data):
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")

@socketio.on('send_message')
def send_dm(data):
    if not current_user.is_authenticated: return
    target_handle, text = data.get('target_handle'), data.get('text')
    if not target_handle or not text: return
    target_user = User.query.filter_by(handle=target_handle).first()
    if not target_user: return
    
    # Only mutual followers can DM
    if not current_user.is_following(target_user) or not target_user.is_following(current_user):
        emit('message_error', {'error': 'You can only message mutual followers'})
        return
        
    conv = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == target_user.id)) |
        ((Conversation.user1_id == target_user.id) & (Conversation.user2_id == current_user.id))
    ).first()
    ts = int(time.time() * 1000)
    if not conv:
        conv = Conversation(user1_id=current_user.id, user2_id=target_user.id, updated_at=ts)
        db.session.add(conv)
        db.session.commit()
    msg = Message(conversation_id=conv.id, sender_id=current_user.id, text=text, timestamp=ts)
    conv.updated_at = ts
    db.session.add(msg)
    
    # Notification for Message
    existing_notif = Notification.query.filter_by(user_id=target_user.id, sender_id=current_user.id, type='message', is_read=False).first()
    if not existing_notif:
        n = Notification(user_id=target_user.id, sender_id=current_user.id, type='message', content=f"{current_user.display_name} sent you a message.", timestamp=ts)
        db.session.add(n)
        socketio.emit('receive_notification', n.to_dict(), room=f"user_{target_user.id}")
        
    db.session.commit()
    
    payload = {
        'id': msg.id, 'text': text, 'timestamp': ts, 'conv_id': conv.id,
        'sender_handle': current_user.handle, 'sender_name': current_user.display_name, 'sender_photo': current_user.profile_photo_url,
        'target_handle': target_handle
    }
    emit('receive_message', payload, room=f"user_{current_user.id}")
    emit('receive_message', payload, room=f"user_{target_user.id}")

@socketio.on('join')
def handle_join(user_data):
    # Fetch top 200 recent posts
    recent_posts = Post.query.order_by(Post.timestamp.desc()).limit(200).all()
    
    # Filter private posts
    visible_posts = []
    followed_handles = []
    viewer_id = None
    if current_user.is_authenticated:
        followed_handles = [u.handle for u in current_user.followed]
        viewer_id = current_user.id
        
    for p in recent_posts:
        user = User.query.filter_by(handle=p.handle).first()
        if user and user.is_private:
            if not current_user.is_authenticated:
                continue
            if p.handle != current_user.handle and p.handle not in followed_handles:
                continue
        visible_posts.append(p)
    
    def get_score(p):
        score = p.likes + (p.bookmarks * 10) + (p.reply_count * 150)
        # Add a tiny bit of recency bias so new posts aren't always strictly at 0 below old 0s
        score += (p.timestamp / 1000000000000.0) 
        user = User.query.filter_by(handle=p.handle).first()
        if user and user.account_tier == 'Premium+':
            score *= 10
        return score
        
    # Sort algorithmically
    visible_posts.sort(key=get_score, reverse=True)
    # Send top 100
    for p in visible_posts[:100]:
        emit('receive_post', post_to_dict(p, viewer_id))

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
            
            # Notification for Reply
            target_user = User.query.filter_by(handle=parent_post.handle).first()
            if target_user and target_user.handle != handle:
                n = Notification(user_id=target_user.id, type='reply', content=f"{sender} replied to your post.", timestamp=int(time.time() * 1000))
                
                # Check if sender is logged in to attach sender_id
                if current_user.is_authenticated:
                    n.sender_id = current_user.id
                    
                db.session.add(n)
                socketio.emit('receive_notification', n.to_dict(), room=f"user_{target_user.id}")
                
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
    
    # Notification for Retweet
    if post.is_retweet and post.original_post_id:
        orig = Post.query.get(post.original_post_id)
        if orig:
            target_user = User.query.filter_by(handle=orig.handle).first()
            if target_user and target_user.handle != handle:
                n = Notification(user_id=target_user.id, type='retweet', content=f"{sender} retweeted your post.", timestamp=int(time.time() * 1000))
                if current_user.is_authenticated:
                    n.sender_id = current_user.id
                db.session.add(n)
                socketio.emit('receive_notification', n.to_dict(), room=f"user_{target_user.id}")
                db.session.commit()
            
    emit('receive_post', post_to_dict(post), broadcast=True)

@socketio.on('bookmark_post')
def handle_bookmark_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post.bookmarks += 1
        db.session.commit()

@socketio.on('like_post')
def handle_like_post(post_id):
    if not current_user.is_authenticated:
        return
    post = Post.query.get(post_id)
    if not post:
        return

    # Check if user already liked this post
    existing_like = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if existing_like:
        # Toggle off — unlike
        db.session.delete(existing_like)
        post.likes = max(0, post.likes - 1)
        db.session.commit()
        emit('update_likes', {'id': post_id, 'likes': post.likes, 'userLiked': False}, broadcast=True)
    else:
        # New like
        new_like = PostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        post.likes += 1

        target_user = User.query.filter_by(handle=post.handle).first()
        if target_user and target_user.id != current_user.id:
            n = Notification(user_id=target_user.id, sender_id=current_user.id, type='like', content=f"{current_user.display_name} liked your post.", timestamp=int(time.time() * 1000))
            db.session.add(n)
            socketio.emit('receive_notification', n.to_dict(), room=f"user_{target_user.id}")

        db.session.commit()
        emit('update_likes', {'id': post_id, 'likes': post.likes, 'userLiked': True}, broadcast=True)

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    try:
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({'reply': '⚡ Rooted AI is not configured yet. Add GEMINI_API_KEY to your environment variables.'})

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        data = request.get_json()
        history = data.get('history', [])[-6:]  # last 6 msgs only to save free-tier tokens
        message = data.get('message', '')

        # Short system prompt to minimise token usage
        system_prompt = "You are Rooted AI \ud83c\udf3f \u2014 a friendly, concise assistant on a nature-inspired social app. Keep replies under 150 words."

        chat_history = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["Got it! I'm Rooted AI \ud83c\udf3f How can I help?"]}
        ]
        for h in history:
            chat_history.append({"role": h['role'], "parts": [h['content']]})

        chat = model.start_chat(history=chat_history)
        response = chat.send_message(message)
        return jsonify({'reply': response.text})
    except Exception as e:
        err = str(e)
        if 'quota' in err.lower() or '429' in err or 'exhausted' in err.lower():
            return jsonify({'reply': '\u23f3 Rooted AI is resting (free tier rate limit). Wait 30\u201360 seconds and try again \ud83c\udf3f'})
        return jsonify({'reply': f'Something went wrong. Please try again shortly.'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

