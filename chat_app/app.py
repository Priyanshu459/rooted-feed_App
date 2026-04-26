import os
from flask import Flask, render_template, request, jsonify, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# 500 MB max upload size
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# Enable SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=500*1024*1024)

# In-memory storage for posts
posts = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'media' not in request.files:
        return jsonify({'error': 'No media part'}), 400
    file = request.files['media']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(f"{int(time.time())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_url = url_for('static', filename=f"uploads/{filename}")
        
        # Determine type
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        media_type = 'video' if ext in ['mp4', 'webm', 'ogg', 'mov'] else 'image'
        
        return jsonify({
            'url': file_url,
            'type': media_type
        })

@socketio.on('join')
def handle_join(user_data):
    # Send all previous posts to the joined user
    for post in posts:
        emit('receive_post', post)

@socketio.on('create_post')
def handle_create_post(data):
    post_id = str(int(time.time() * 1000))
    post = {
        'id': post_id,
        'sender': data.get('sender', 'Anonymous'),
        'handle': data.get('handle', '@user'),
        'text': data.get('text', ''),
        'mediaUrl': data.get('mediaUrl'),
        'mediaType': data.get('mediaType'),
        'timestamp': int(time.time() * 1000),
        'likes': 0
    }
    posts.insert(0, post) # Newest first in memory, though clients handle ordering
    emit('receive_post', post, broadcast=True)

@socketio.on('like_post')
def handle_like_post(post_id):
    for post in posts:
        if post['id'] == post_id:
            post['likes'] += 1
            emit('update_likes', {'id': post_id, 'likes': post['likes']}, broadcast=True)
            break

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

