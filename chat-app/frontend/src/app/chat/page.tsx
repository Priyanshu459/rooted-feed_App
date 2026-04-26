'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { io, Socket } from 'socket.io-client';

interface Message {
  id: string;
  sender: string;
  text?: string;
  mediaUrl?: string;
  mediaType?: 'image' | 'video';
  timestamp: number;
}

export default function ChatPage() {
  const router = useRouter();
  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [socket, setSocket] = useState<Socket | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedPhone = localStorage.getItem('userPhone');
    if (!storedPhone) {
      router.push('/');
      return;
    }
    setPhoneNumber(storedPhone);

    // Connect to backend
    const newSocket = io('http://localhost:3001');
    setSocket(newSocket);

    newSocket.emit('join', storedPhone);

    newSocket.on('receive_message', (msg: Message) => {
      setMessages((prev) => [...prev, msg]);
    });

    return () => {
      newSocket.disconnect();
    };
  }, [router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputText.trim() || !socket) return;

    const newMsg: Message = {
      id: Date.now().toString(),
      sender: phoneNumber,
      text: inputText,
      timestamp: Date.now(),
    };

    socket.emit('send_message', newMsg);
    setInputText('');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !socket) return;

    // Local check for size (500MB)
    if (file.size > 500 * 1024 * 1024) {
      alert('File size exceeds 500MB limit.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('media', file);
    formData.append('sender', phoneNumber);

    try {
      // Create a mock upload request using XHR to track progress
      const xhr = new XMLHttpRequest();
      xhr.open('POST', 'http://localhost:3001/upload', true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        if (xhr.status === 200) {
          const data = JSON.parse(xhr.responseText);
          // Emitting the message with media is handled by the server upon successful upload in our mock, 
          // or we can emit it here. Let's let the server broadcast it.
        } else {
          alert('Upload failed');
        }
        setUploading(false);
        setUploadProgress(0);
        if (fileInputRef.current) fileInputRef.current.value = '';
      };

      xhr.onerror = () => {
        alert('Upload failed due to network error.');
        setUploading(false);
        setUploadProgress(0);
        if (fileInputRef.current) fileInputRef.current.value = '';
      };

      xhr.send(formData);

    } catch (error) {
      console.error(error);
      setUploading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      maxWidth: '1200px',
      margin: '0 auto',
      backgroundColor: 'var(--bg-primary)',
      boxShadow: 'var(--shadow-lg)'
    }}>
      {/* Sidebar */}
      <div style={{
        width: '300px',
        borderRight: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-secondary)',
        padding: '24px'
      }}>
        <h2 style={{ color: 'var(--accent-color)', marginBottom: '24px' }}>Earthly</h2>
        <div className="glass" style={{
          padding: '16px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '16px'
        }}>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Logged in as</p>
          <p style={{ fontWeight: 500 }}>{phoneNumber}</p>
        </div>
        <button 
          className="btn-primary" 
          onClick={() => {
            localStorage.removeItem('userPhone');
            router.push('/');
          }}
          style={{ width: '100%', backgroundColor: 'var(--text-secondary)' }}
        >
          Disconnect
        </button>
      </div>

      {/* Main Chat Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg-primary)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-color)',
          backgroundColor: 'var(--glass-bg)',
          backdropFilter: 'blur(10px)',
          position: 'sticky',
          top: 0,
          zIndex: 10
        }}>
          <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>Global Chat (Mock)</h3>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)' }}>
            Chatting with everyone connected
          </p>
        </div>

        {/* Messages List */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {messages.map((msg) => {
            const isMe = msg.sender === phoneNumber;
            return (
              <div key={msg.id} style={{
                alignSelf: isMe ? 'flex-end' : 'flex-start',
                maxWidth: '70%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: isMe ? 'flex-end' : 'flex-start'
              }}>
                {!isMe && <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px', marginLeft: '4px' }}>{msg.sender}</span>}
                <div style={{
                  backgroundColor: isMe ? 'var(--chat-bubble-me)' : 'var(--chat-bubble-other)',
                  padding: '12px 16px',
                  borderRadius: isMe ? '16px 16px 0 16px' : '16px 16px 16px 0',
                  boxShadow: 'var(--shadow-sm)',
                  wordBreak: 'break-word'
                }}>
                  {msg.mediaUrl && (
                    <div style={{ marginBottom: msg.text ? '8px' : '0' }}>
                      {msg.mediaType === 'image' ? (
                        <img src={`http://localhost:3001${msg.mediaUrl}`} alt="attachment" style={{ maxWidth: '100%', borderRadius: '8px' }} />
                      ) : (
                        <video src={`http://localhost:3001${msg.mediaUrl}`} controls style={{ maxWidth: '100%', borderRadius: '8px' }} />
                      )}
                    </div>
                  )}
                  {msg.text && <p style={{ margin: 0 }}>{msg.text}</p>}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{
          padding: '20px 24px',
          backgroundColor: 'var(--bg-secondary)',
          borderTop: '1px solid var(--border-color)'
        }}>
          {uploading && (
            <div style={{ marginBottom: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              Uploading... {uploadProgress}%
              <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--border-color)', borderRadius: '2px', marginTop: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${uploadProgress}%`, height: '100%', backgroundColor: 'var(--accent-color)', transition: 'width 0.2s' }} />
              </div>
            </div>
          )}
          <form onSubmit={sendMessage} style={{ display: 'flex', gap: '12px' }}>
            <input
              type="file"
              accept="image/*,video/*"
              style={{ display: 'none' }}
              ref={fileInputRef}
              onChange={handleFileUpload}
            />
            <button
              type="button"
              className="btn-primary"
              style={{ padding: '0 16px', backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              title="Attach File (Max 500MB)"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
              </svg>
            </button>
            <input
              type="text"
              className="input-field"
              placeholder="Type a message..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              style={{ flex: 1 }}
            />
            <button type="submit" className="btn-primary" disabled={!inputText.trim() && !uploading}>
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
