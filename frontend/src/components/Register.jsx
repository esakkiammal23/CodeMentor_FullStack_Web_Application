import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import API from '../api';

export default function Register({ onLogin }) {
  const [form, setForm] = useState({
    email: '', username: '', full_name: '', password: '', preferred_language: 'english'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res = await API.post('/users/register/', form);
      onLogin(res.data.user, res.data.token);
    } catch (err) {
      const errs = err.response?.data;
      setError(typeof errs === 'object' ? Object.values(errs).flat().join(' ') : 'Registration failed.');
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">🎓 CodeMentor</h1>
        <p className="auth-subtitle">Create your free account</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input className="form-input" name="full_name" value={form.full_name}
              onChange={handle} required placeholder="Your full name" />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" name="email" value={form.email}
              onChange={handle} required placeholder="you@email.com" />
          </div>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input className="form-input" name="username" value={form.username}
              onChange={handle} required placeholder="username123" />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" name="password" value={form.password}
              onChange={handle} required placeholder="Min 6 characters" />
          </div>
          <div className="form-group">
            <label className="form-label">Preferred Teaching Language</label>
            <select className="form-select" name="preferred_language"
              value={form.preferred_language} onChange={handle}>
              <option value="english">English</option>
              <option value="tamil">Tamil (தமிழ்)</option>
              <option value="hindi">Hindi (हिंदी)</option>
              <option value="tanglish">Tanglish</option>
            </select>
          </div>
          <button className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>
        <p className="text-center text-muted mt-4">
          Have account? <Link to="/login" style={{ color: '#a78bfa' }}>Login here</Link>
        </p>
      </div>
    </div>
  );
}