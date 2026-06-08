import React, { useEffect, useState } from 'react';
import API from '../api';

const LANG_NAMES = { python: 'Python', java: 'Java', ai: 'Artificial Intelligence', ml: 'Machine Learning' };
const LANG_ICONS = { python: '🐍', java: '☕', ai: '🤖', ml: '📊' };

export default function Certificates() {
  const [certs, setCerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get('/certificates/my/')
      .then(res => setCerts(res.data.certificates))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card"><div className="spinner" /></div>;

  return (
    <div>
      <div className="card">
        <h2 className="card-title">🏆 My Certificates</h2>
        <p className="text-muted">Certificates are awarded when you score 17 or more out of 20.</p>
      </div>
      {certs.length === 0 ? (
        <div className="card text-center">
          <p style={{ fontSize: '3rem', marginBottom: '12px' }}>🎯</p>
          <p className="text-muted">No certificates yet. Pass a test to earn one!</p>
        </div>
      ) : (
        certs.map(cert => (
          <div key={cert.id} className="cert-card">
            <div className="cert-info">
              <h3>{LANG_ICONS[cert.language]} {LANG_NAMES[cert.language] || cert.language}</h3>
              <p>Score: {cert.score}/20 &nbsp;|&nbsp; Issued: {cert.issued_at}</p>
              <p>Certificate ID: <code style={{ color: '#a78bfa' }}>{cert.certificate_id}</code></p>
              {cert.email_sent && <p style={{ color: '#6ee7b7', fontSize: '0.82rem' }}>✉️ Sent to your email</p>}
            </div>
            <div>
              <a href={`http://localhost:8000${cert.pdf_url}`} target="_blank"
                rel="noreferrer" className="btn btn-primary">
                📄 Download PDF
              </a>
            </div>
          </div>
        ))
      )}
    </div>
  );
}