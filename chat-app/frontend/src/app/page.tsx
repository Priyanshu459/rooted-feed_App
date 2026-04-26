'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber) return;
    
    setLoading(true);
    // Mock login flow
    setTimeout(() => {
      localStorage.setItem('userPhone', phoneNumber);
      router.push('/chat');
    }, 1000);
  };

  return (
    <main style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '20px'
    }}>
      <div className="glass" style={{
        padding: '40px',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        width: '100%',
        maxWidth: '400px',
        textAlign: 'center'
      }}>
        <h1 style={{ marginBottom: '8px', color: 'var(--accent-color)', fontSize: '28px' }}>
          Earthly Chat
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
          Connect naturally.
        </p>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ textAlign: 'left' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500 }}>
              Phone Number
            </label>
            <input
              type="tel"
              className="input-field"
              placeholder="+1 (555) 000-0000"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '8px' }}>
            {loading ? 'Joining...' : 'Join Chat'}
          </button>
        </form>
      </div>
    </main>
  );
}
