import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import API from '../api';

const LANGUAGES = [
  { key: 'python', name: 'Python', icon: '🐍' },
  { key: 'java', name: 'Java', icon: '☕' },
  { key: 'ai', name: 'Artificial Intelligence', icon: '🤖' },
  { key: 'ml', name: 'Machine Learning', icon: '📊' },
];

export default function Dashboard({ user }) {
  const [progresses, setProgresses] = useState({});

  useEffect(() => {
    LANGUAGES.forEach(async (lang) => {
      try {
        const res = await API.get(`/courses/progress/?language=${lang.key}`);
        setProgresses(prev => ({ ...prev, [lang.key]: res.data }));
      } catch (e) {}
    });
  }, []);

  return (
    <div>
      <div className="card">
        <h2 className="card-title">Welcome back, {user.full_name || user.username}! 👋</h2>
        <p className="text-muted">Choose a programming language to learn or continue where you left off.</p>
      </div>

      <h3 style={{ color: '#fff', marginBottom: '16px' }}>📚 Your Courses</h3>
      <div className="lang-grid">
        {LANGUAGES.map(lang => {
          const p = progresses[lang.key];
          return (
            <div key={lang.key} className="lang-card">
              <div className="lang-icon">{lang.icon}</div>
              <div className="lang-name">{lang.name}</div>
              {p && (
                <>
                  <div className="progress-bar-wrap" style={{ marginTop: '12px' }}>
                    <div className="progress-bar-fill" style={{ width: `${p.percentage}%` }} />
                  </div>
                  <p className="text-muted mt-2">{p.completed_topics}/{p.total_topics} topics done</p>
                  {p.all_completed && (
                    <span className="topic-badge badge-done" style={{ marginTop: '8px', display: 'inline-block' }}>
                      ✓ Ready to Test!
                    </span>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex gap-2 flex-wrap mt-4">
        <Link to="/learn" className="btn btn-primary">📖 Start Learning</Link>
        <Link to="/test" className="btn btn-outline">📝 Take a Test</Link>
        <Link to="/certificates" className="btn btn-success">🏆 My Certificates</Link>
      </div>
    </div>
  );
}