
import React, { useState, useEffect, useRef } from 'react';
import API from '../api';

/* ═══════════════════════════════════════════════════════════════
   MODAL WRAPPER
═══════════════════════════════════════════════════════════════ */
function Modal({ onClose, children }) {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.80)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        background: '#12172b',
        border: '1px solid #2a3558',
        borderRadius: 20,
        padding: '2rem',
        width: '100%', maxWidth: 460,
        maxHeight: '92vh', overflowY: 'auto',
        position: 'relative',
        animation: 'lpModalIn .22s ease',
        boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
      }}>
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 14, right: 14,
            background: '#1e2540', border: '1px solid #2a3558',
            color: '#94a3b8', width: 30, height: 30, borderRadius: 8,
            cursor: 'pointer', fontSize: '1rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >✕</button>
        {children}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   LOGIN FORM
═══════════════════════════════════════════════════════════════ */
function LoginForm({ onLogin, onSwitch, onClose }) {
  const [form, setForm]       = useState({ email: '', password: '' });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async e => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res = await API.post('/users/login/', form);
      onLogin(res.data.user, res.data.token);
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Check credentials.');
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '.3rem' }}>🎓</div>
        <h2 style={styles.mTitle}>Welcome Back</h2>
        <p style={styles.mSub}>Login to continue your learning journey</p>
      </div>

      {error && <div style={styles.errBox}>{error}</div>}

      <form onSubmit={submit}>
        {[
          { name: 'email',    label: 'Email',    type: 'email',    ph: 'you@email.com' },
          { name: 'password', label: 'Password', type: 'password', ph: '••••••••' },
        ].map(f => (
          <div key={f.name} style={{ marginBottom: '1rem' }}>
            <label style={styles.label}>{f.label}</label>
            <input
              type={f.type} required placeholder={f.ph}
              value={form[f.name]}
              onChange={e => setForm({ ...form, [f.name]: e.target.value })}
              style={styles.input}
              onFocus={e => e.target.style.borderColor = '#00d4ff'}
              onBlur={e  => e.target.style.borderColor = '#2a3558'}
            />
          </div>
        ))}
        <button type="submit" disabled={loading} style={{ ...styles.btnPrimary, width: '100%', marginTop: '.25rem' }}>
          {loading ? 'Logging in…' : 'Login →'}
        </button>
      </form>

      <p style={styles.switchTxt}>
        No account?{' '}
        <span onClick={onSwitch} style={styles.switchLink}>Register here</span>
      </p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   REGISTER FORM
═══════════════════════════════════════════════════════════════ */
function RegisterForm({ onLogin, onSwitch, onClose }) {
  const [form, setForm] = useState({
    email: '', username: '', full_name: '', password: '', preferred_language: 'english',
  });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async e => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res = await API.post('/users/register/', form);
      onLogin(res.data.user, res.data.token);
      onClose();
    } catch (err) {
      const d = err.response?.data;
      setError(typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Registration failed.');
    }
    setLoading(false);
  };

  const fields = [
    { name: 'full_name', label: 'Full Name', type: 'text',     ph: 'Your full name'    },
    { name: 'email',     label: 'Email',     type: 'email',    ph: 'you@email.com'      },
    { name: 'username',  label: 'Username',  type: 'text',     ph: 'username123'        },
    { name: 'password',  label: 'Password',  type: 'password', ph: 'Min 6 characters'  },
  ];

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '.3rem' }}>🚀</div>
        <h2 style={styles.mTitle}>Create Account</h2>
        <p style={styles.mSub}>Start your AI-powered coding journey today</p>
      </div>

      {error && <div style={styles.errBox}>{error}</div>}

      <form onSubmit={submit}>
        {fields.map(f => (
          <div key={f.name} style={{ marginBottom: '1rem' }}>
            <label style={styles.label}>{f.label}</label>
            <input
              type={f.type} required placeholder={f.ph}
              value={form[f.name]}
              onChange={e => setForm({ ...form, [f.name]: e.target.value })}
              style={styles.input}
              onFocus={e => e.target.style.borderColor = '#00d4ff'}
              onBlur={e  => e.target.style.borderColor = '#2a3558'}
            />
          </div>
        ))}

        <div style={{ marginBottom: '1.25rem' }}>
          <label style={styles.label}>Preferred Teaching Language</label>
          <select
            value={form.preferred_language}
            onChange={e => setForm({ ...form, preferred_language: e.target.value })}
            style={{ ...styles.input, cursor: 'pointer' }}
          >
            <option value="english">English</option>
            <option value="tamil">Tamil (தமிழ்)</option>
            <option value="hindi">Hindi (हिंदी)</option>
            <option value="tanglish">Tanglish</option>
            <option value="malayalam">Malayalam (മലയാളം)</option>
          </select>
        </div>

        <button type="submit" disabled={loading} style={{ ...styles.btnPrimary, width: '100%' }}>
          {loading ? 'Creating account…' : 'Create Account →'}
        </button>
      </form>

      <p style={styles.switchTxt}>
        Have an account?{' '}
        <span onClick={onSwitch} style={styles.switchLink}>Login here</span>
      </p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   FEEDBACK FORM
═══════════════════════════════════════════════════════════════ */
function FeedbackForm({ onClose, onSubmit }) {
  const [form, setForm] = useState({ name: '', role: '', rating: '5', text: '' });
  const [done, setDone] = useState(false);
  const handle = e => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = e => {
    e.preventDefault();
    onSubmit({ ...form, rating: Number(form.rating) });
    setDone(true);
  };

  if (done) return (
    <div style={{ textAlign: 'center', padding: '2rem' }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎉</div>
      <h3 style={{ color: '#10b981', marginBottom: '.5rem' }}>Thank you!</h3>
      <p style={{ color: '#94a3b8' }}>Your feedback is now live on the page!</p>
      <button onClick={onClose} style={{ ...styles.btnPrimary, marginTop: '1.5rem' }}>Close</button>
    </div>
  );

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <div style={{ fontSize: '2rem', marginBottom: '.3rem' }}>💬</div>
        <h2 style={styles.mTitle}>Submit Feedback</h2>
        <p style={styles.mSub}>Tell us about your experience</p>
      </div>
      <form onSubmit={submit}>
        {[
          { name: 'name', label: 'Your Name', ph: 'Aravind Kumar', type: 'text' },
          { name: 'role', label: 'Role',       ph: 'CSE Student, Chennai', type: 'text' },
        ].map(f => (
          <div key={f.name} style={{ marginBottom: '1rem' }}>
            <label style={styles.label}>{f.label}</label>
            <input type={f.type} name={f.name} required placeholder={f.ph}
              value={form[f.name]} onChange={handle} style={styles.input}
              onFocus={e => e.target.style.borderColor = '#00d4ff'}
              onBlur={e  => e.target.style.borderColor = '#2a3558'} />
          </div>
        ))}
        <div style={{ marginBottom: '1rem' }}>
          <label style={styles.label}>Rating</label>
          <select name="rating" value={form.rating} onChange={handle}
            style={{ ...styles.input, cursor: 'pointer' }}>
            {[5,4,3,2,1].map(n => (
              <option key={n} value={n}>{'★'.repeat(n)}{'☆'.repeat(5-n)} ({n}/5)</option>
            ))}
          </select>
        </div>
        <div style={{ marginBottom: '1.25rem' }}>
          <label style={styles.label}>Your Feedback</label>
          <textarea name="text" required rows={4} placeholder="Share your experience…"
            value={form.text} onChange={handle}
            style={{ ...styles.input, resize: 'vertical', lineHeight: 1.6 }}
            onFocus={e => e.target.style.borderColor = '#00d4ff'}
            onBlur={e  => e.target.style.borderColor = '#2a3558'} />
        </div>
        <button type="submit" style={{ ...styles.btnPrimary, width: '100%' }}>
          Submit Feedback
        </button>
      </form>
    </div>
  );
}

/* ── shared micro-styles ── */
const styles = {
  mTitle:     { fontSize: '1.6rem', fontWeight: 700, color: '#e2e8f0', marginBottom: '.3rem' },
  mSub:       { color: '#94a3b8', fontSize: '.875rem' },
  label:      { display: 'block', marginBottom: '.4rem', fontSize: '.85rem', color: '#94a3b8' },
  input:      {
    width: '100%', background: '#0f1422', border: '1px solid #2a3558',
    borderRadius: 8, padding: '.65rem .9rem', color: '#e2e8f0',
    fontFamily: 'Sora, Segoe UI, sans-serif', fontSize: '.9rem',
    outline: 'none', boxSizing: 'border-box', transition: 'border-color .2s',
  },
  errBox:     {
    background: 'rgba(239,68,68,.14)', border: '1px solid rgba(239,68,68,.4)',
    borderRadius: 8, padding: '.75rem 1rem', fontSize: '.85rem',
    color: '#fca5a5', marginBottom: '1rem',
  },
  btnPrimary: {
    padding: '.65rem 1.5rem', borderRadius: 8,
    background: '#00d4ff', color: '#0a0e1a',
    border: 'none', fontWeight: 700, fontSize: '.95rem',
    cursor: 'pointer', fontFamily: 'Sora, sans-serif',
    transition: 'all .2s', letterSpacing: '.01em',
  },
  switchTxt:  { textAlign: 'center', fontSize: '.875rem', color: '#94a3b8', marginTop: '1.25rem' },
  switchLink: { color: '#00d4ff', cursor: 'pointer', fontWeight: 600 },
};

/* ═══════════════════════════════════════════════════════════════
   LANDING PAGE
═══════════════════════════════════════════════════════════════ */
export default function LandingPage({ onLogin, startModal }) {
  const [modal, setModal] = useState(startModal || null);
    const [userFeedbacks, setUserFeedbacks] = useState([]);

  useEffect(() => {
    if (startModal) setModal(startModal);
  }, [startModal]);

  const close = () => setModal(null);

  const scrollTo = id => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  /* ── inline styles so the landing page is completely self-contained ── */
  const R = {                                           // root
    fontFamily: "'Sora', 'Segoe UI', sans-serif",
    background: '#0a0e1a',
    color: '#e2e8f0',
    minHeight: '100vh',
    overflowX: 'hidden',
  };

  const NAV = {
    position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
    height: 64, padding: '0 2rem',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    background: 'rgba(10,14,26,0.93)',
    backdropFilter: 'blur(16px)',
    borderBottom: '1px solid #2a3558',
  };

  const LOGO = {
    fontFamily: "'Space Mono', monospace",
    fontSize: '1.15rem', color: '#00d4ff',
    display: 'flex', alignItems: 'center', gap: '.5rem',
    textDecoration: 'none', cursor: 'pointer',
  };

  const BTN_OUT = {
    padding: '.45rem 1.1rem', borderRadius: 8,
    background: 'transparent', border: '1px solid #2a3558',
    color: '#94a3b8', fontFamily: 'Sora, sans-serif',
    fontSize: '.875rem', fontWeight: 600, cursor: 'pointer',
    transition: 'all .2s',
  };
  const BTN_PRI = {
    ...BTN_OUT, background: '#00d4ff',
    color: '#0a0e1a', border: 'none',
  };
  const BTN_LG = { padding: '.75rem 2rem', fontSize: '1rem' };

  const LINK_BTN = {
    background: 'none', border: 'none',
    color: '#94a3b8', fontFamily: 'Sora, sans-serif',
    fontSize: '.875rem', fontWeight: 500, cursor: 'pointer',
    transition: 'color .2s', padding: 0,
  };

  const SECTION = {
    padding: '5rem 2rem', maxWidth: 1200, margin: '0 auto',
  };

  const CARD = {
    background: '#1a2035', border: '1px solid #2a3558',
    borderRadius: 16, padding: '1.5rem',
  };

  const features = [
    { icon: '🌐', t: '5 Interface Languages',  d: 'Tamil, English, Hindi, Malayalam, Tanglish — learn in your language.' },
    { icon: '🤖', t: '24/7 AI Tutor',           d: 'Ask any doubt anytime. Instant AI explanations, always available.' },
    { icon: '📝', t: 'Topic Tests (10 Q)',       d: 'Score 7/10 to advance. AI detects weak areas and guides revision.' },
    { icon: '🏆', t: 'Leaderboard',              d: 'Compete with peers on topic scores. Climb the ranks.' },
    { icon: '🎓', t: 'Smart Certificate',        d: 'Score 17/20 on the final test. Auto-certificate sent to your email.' },
    { icon: '🧠', t: 'Weak Topic Detection',     d: 'AI finds where you struggle and blocks advancement until mastered.' },
    { icon: '🔒', t: 'Anti-Cheat Exams',         d: 'Timed exams with tab-switch detection for fair assessment.' },
    { icon: '📊', t: 'Progress Tracking',        d: 'Visual progress bars for every course and topic.' },
  ];

  const steps = [
    { n: '01', t: 'Choose a Course',     d: 'Pick Python, Java, AI, or ML. Select your interface language.' },
    { n: '02', t: 'Learn Topic by Topic', d: 'Read AI lessons. Ask doubts in the built-in chatbot.' },
    { n: '03', t: 'Take Topic Test',      d: 'Answer 10 questions. Score 7+ to unlock the next topic.' },
    { n: '04', t: 'Complete Course Test', d: 'After all topics, take the 20-question final test.' },
    { n: '05', t: 'Get Certificate',      d: 'Score 17/20 → certificate generated and emailed instantly.' },
  ];

  const testimonials = [
    { s: 5, text: '"Learning Python in Tamil was a dream. The AI explained recursion so clearly — something textbooks never could."',    name: 'Aravind Kumar', role: 'CSE Student, Chennai'  },
    { s: 5, text: '"The topic-wise test system is brilliant. I could see exactly where I was weak and the AI helped me fix it!"',          name: 'Priya Menon',   role: 'MCA Student, Kerala'   },
    { s: 4, text: '"Leaderboard keeps me motivated. Seeing my rank go up made me study harder. Completed all 12 Python topics!"',          name: 'Ravi Shankar',  role: 'B.Tech 3rd Year'       },
    { s: 5, text: '"Got my Java certificate in a week. The anti-cheat system made the exam feel real and the certificate actually means something."', name: 'Sneha Iyer', role: 'Fresher, Bangalore' },
  ];

  return (
    <>
      {/* keyframes injected once */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=Space+Mono:wght@400;700&family=JetBrains+Mono:wght@400;600&display=swap');
        @keyframes lpModalIn { from{transform:scale(.95);opacity:0} to{transform:scale(1);opacity:1} }
        @keyframes lpFadeUp  { from{transform:translateY(30px);opacity:0} to{transform:translateY(0);opacity:1} }
        @keyframes lpGlow    { 0%,100%{opacity:.5} 50%{opacity:1} }
        .lp-nav-a:hover { color:#00d4ff !important; }
        .lp-btn-out:hover { border-color:#00d4ff !important; color:#00d4ff !important; }
        .lp-btn-pri:hover { box-shadow:0 0 20px rgba(0,212,255,0.4) !important; transform:translateY(-1px) !important; }
        .lp-feat:hover { border-color:#00d4ff !important; transform:translateY(-3px) !important; box-shadow:0 0 20px rgba(0,212,255,0.2) !important; }
        .lp-step:hover { border-color:#7c3aed !important; }
        .lp-fb:hover   { border-color:#7c3aed !important; }
        .lp-footer-a:hover { color:#00d4ff !important; }
      `}</style>

      <div style={R}>

        {/* ── NAVBAR ─────────────────────────────────────────── */}
        <nav style={NAV}>
          <div style={LOGO} onClick={() => scrollTo('home')}>
            &lt;/&gt; <span style={{ color: '#e2e8f0' }}>CodeMentor</span>
          </div>

          {/* Desktop nav links */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
            {[
              { l: 'Features',          a: () => scrollTo('features') },
              { l: 'How it Works',      a: () => scrollTo('howitworks') },
              { l: 'Students Feedback', a: () => scrollTo('feedback') },
              { l: 'About',             a: () => scrollTo('about') },
            ].map(x => (
              <button key={x.l} onClick={x.a}
                className="lp-nav-a"
                style={{ ...LINK_BTN, color: '#94a3b8' }}>
                {x.l}
              </button>
            ))}
            <button className="lp-nav-a" style={{ ...LINK_BTN, color: '#94a3b8' }}
              onClick={() => setModal('feedback')}>
              Submit Feedback
            </button>
          </div>

          {/* Auth buttons */}
          <div style={{ display: 'flex', gap: '.75rem' }}>
            <button className="lp-btn-out" style={BTN_OUT} onClick={() => setModal('login')}>
              Login
            </button>
            <button className="lp-btn-pri" style={BTN_PRI} onClick={() => setModal('register')}>
              Register
            </button>
          </div>
        </nav>

        {/* ── HERO ───────────────────────────────────────────── */}
        <section id="home" style={{
          minHeight: '100vh', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          textAlign: 'center', padding: '7rem 2rem 4rem',
          position: 'relative', overflow: 'hidden',
        }}>
          {/* grid bg */}
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            backgroundImage: 'linear-gradient(rgba(0,212,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,.04) 1px,transparent 1px)',
            backgroundSize: '50px 50px',
          }} />
          {/* glow */}
          <div style={{
            position: 'absolute', top: '18%', left: '50%', transform: 'translateX(-50%)',
            width: 600, height: 300, pointerEvents: 'none',
            background: 'radial-gradient(ellipse,rgba(0,212,255,.12) 0%,transparent 70%)',
            animation: 'lpGlow 4s ease-in-out infinite',
          }} />

          {/* Badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '.5rem',
            background: 'rgba(0,212,255,.1)', border: '1px solid rgba(0,212,255,.3)',
            padding: '.35rem 1rem', borderRadius: 999, fontSize: '.8rem',
            color: '#00d4ff', fontFamily: "'Space Mono',monospace", marginBottom: '1.5rem',
            position: 'relative',
          }}>
            🚀 AI Powered Learning
          </div>

          <h1 style={{
            fontSize: 'clamp(2.5rem,6vw,4.5rem)', fontWeight: 800,
            lineHeight: 1.1, marginBottom: '1.5rem', maxWidth: 820,
            position: 'relative',
          }}>
            Learn Coding with{' '}
            <span style={{
              background: 'linear-gradient(135deg,#00d4ff,#7c3aed)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              AI Tutor
            </span>
          </h1>

          <p style={{
            fontSize: '1.1rem', color: '#94a3b8', maxWidth: 560,
            lineHeight: 1.7, marginBottom: '2.5rem', position: 'relative',
          }}>
            Topic-wise lessons, real-time AI doubt solving, anti-cheat tests, and smart certificates — all in your language.
          </p>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center', position: 'relative' }}>
            <button className="lp-btn-pri" style={{ ...BTN_PRI, ...BTN_LG }}
              onClick={() => setModal('register')}>
              🚀 Get Started Free
            </button>
            <button className="lp-btn-out" style={{ ...BTN_OUT, ...BTN_LG }}
              onClick={() => scrollTo('features')}>
              Explore Features
            </button>
          </div>

          {/* Stats */}
          <div style={{
            display: 'flex', gap: '3rem', marginTop: '4rem', flexWrap: 'wrap',
            justifyContent: 'center', position: 'relative',
          }}>
            {[
              { n: '10K+', l: 'Students'  },
              { n: '500+', l: 'Questions' },
              { n: '50+',  l: 'Topics'    },
              { n: '5',    l: 'Languages' },
            ].map(s => (
              <div key={s.l} style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: "'Space Mono',monospace", fontSize: '2rem', color: '#00d4ff', fontWeight: 700 }}>
                  {s.n}
                </div>
                <div style={{ fontSize: '.8rem', color: '#64748b', marginTop: '.25rem' }}>{s.l}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── FEATURES ───────────────────────────────────────── */}
        <section id="features" style={{ ...SECTION, borderTop: '1px solid #2a3558' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '.5rem',
              background: 'rgba(0,212,255,.1)', border: '1px solid rgba(0,212,255,.3)',
              padding: '.3rem .9rem', borderRadius: 999, fontSize: '.78rem',
              color: '#00d4ff', fontFamily: "'Space Mono',monospace", marginBottom: '1rem',
            }}>Features</div>
            <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '.5rem' }}>
              Everything to Learn Coding
            </h2>
            <p style={{ color: '#94a3b8' }}>Built for beginners, powered by AI</p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))',
            gap: '1.5rem',
          }}>
            {features.map(f => (
              <div key={f.t} className="lp-feat" style={{
                ...CARD, cursor: 'default', transition: 'all .3s',
              }}>
                <div style={{ fontSize: '1.75rem', marginBottom: '.75rem' }}>{f.icon}</div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '.5rem' }}>{f.t}</h3>
                <p style={{ fontSize: '.85rem', color: '#94a3b8', lineHeight: 1.6 }}>{f.d}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── HOW IT WORKS ───────────────────────────────────── */}
        <section id="howitworks" style={{
          ...SECTION,
          background: 'rgba(15,20,34,.7)',
          borderRadius: 24,
          margin: '0 auto',
        }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center',
              background: 'rgba(0,212,255,.1)', border: '1px solid rgba(0,212,255,.3)',
              padding: '.3rem .9rem', borderRadius: 999, fontSize: '.78rem',
              color: '#00d4ff', fontFamily: "'Space Mono',monospace", marginBottom: '1rem',
            }}>Workflow</div>
            <h2 style={{ fontSize: '2rem', fontWeight: 700 }}>How It Works</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: 700, margin: '0 auto' }}>
            {steps.map(s => (
              <div key={s.n} className="lp-step" style={{
                display: 'flex', gap: '1.25rem', alignItems: 'flex-start',
                ...CARD, transition: 'border-color .2s',
              }}>
                <div style={{
                  fontFamily: "'Space Mono',monospace", fontSize: '1.1rem',
                  fontWeight: 700, color: '#00d4ff', flexShrink: 0, minWidth: 36,
                }}>
                  {s.n}
                </div>
                <div>
                  <h4 style={{ fontWeight: 600, fontSize: '.95rem', marginBottom: '.3rem' }}>{s.t}</h4>
                  <p style={{ fontSize: '.85rem', color: '#94a3b8', lineHeight: 1.6 }}>{s.d}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── ABOUT ──────────────────────────────────────────── */}
        <section id="about" style={{ ...SECTION, borderTop: '1px solid #2a3558' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr',
            gap: '3rem', alignItems: 'center',
          }}>
            <div>
              <div style={{
                display: 'inline-flex', background: 'rgba(0,212,255,.1)',
                border: '1px solid rgba(0,212,255,.3)', padding: '.3rem .9rem',
                borderRadius: 999, fontSize: '.78rem', color: '#00d4ff',
                fontFamily: "'Space Mono',monospace", marginBottom: '1rem',
              }}>About</div>
              <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1rem' }}>
                Why CodeMentor?
              </h2>
              <p style={{ color: '#94a3b8', lineHeight: 1.8, marginBottom: '1rem' }}>
                CodeMentor was built to break language barriers in programming education.
                Whether you speak Tamil, Hindi, Malayalam, or English — you deserve
                world-class programming education in your own language.
              </p>
              <p style={{ color: '#94a3b8', lineHeight: 1.8 }}>
                Our AI tutor is always available — no scheduled classes, no waiting.
                Just open the app, ask your doubt, and get a clear explanation instantly.
              </p>
            </div>

            {/* Code card */}
            <div style={{
              ...CARD,
              fontFamily: "'JetBrains Mono',monospace",
              fontSize: '.82rem', lineHeight: 1.9, color: '#94a3b8',
            }}>
              <div style={{ color: '#64748b', marginBottom: '.5rem', fontSize: '.75rem' }}>// your learning journey</div>
              <div><span style={{ color: '#7c3aed' }}>const</span> <span style={{ color: '#e2e8f0' }}>journey</span> <span style={{ color: '#f59e0b' }}>=</span> {'{'}</div>
              <div style={{ paddingLeft: '1rem' }}>
                <div><span style={{ color: '#7c3aed' }}>language</span>: <span style={{ color: '#10b981' }}>"Python"</span>,</div>
                <div><span style={{ color: '#7c3aed' }}>tutor</span>: <span style={{ color: '#10b981' }}>"AI (24/7)"</span>,</div>
                <div><span style={{ color: '#7c3aed' }}>topics</span>: <span style={{ color: '#f59e0b' }}>12</span>,</div>
                <div><span style={{ color: '#7c3aed' }}>certificate</span>: <span style={{ color: '#00d4ff' }}>true</span>,</div>
                <div><span style={{ color: '#7c3aed' }}>yourLanguage</span>: <span style={{ color: '#10b981' }}>"Tamil"</span></div>
              </div>
              <div>{'};'}</div>
              <div style={{ marginTop: '.5rem' }}>
                <span style={{ color: '#f59e0b' }}>await</span>{' '}
                <span style={{ color: '#7c3aed' }}>CodeMentor</span>.<span style={{ color: '#e2e8f0' }}>start</span>(journey);
              </div>
              <div style={{ color: '#10b981', marginTop: '.5rem', fontSize: '.78rem' }}>// ✅ Learning started!</div>
            </div>
          </div>
        </section>

        {/* ── TESTIMONIALS ───────────────────────────────────── */}
        <section id="feedback" style={{ ...SECTION, borderTop: '1px solid #2a3558' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <div style={{
              display: 'inline-flex', background: 'rgba(0,212,255,.1)',
              border: '1px solid rgba(0,212,255,.3)', padding: '.3rem .9rem',
              borderRadius: 999, fontSize: '.78rem', color: '#00d4ff',
              fontFamily: "'Space Mono',monospace", marginBottom: '1rem',
            }}>Testimonials</div>
            <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '.5rem' }}>
              What Students Say
            </h2>
            <p style={{ color: '#94a3b8' }}>Real feedback from learners who leveled up with CodeMentor.</p>
          </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: '1.5rem' }}>

            {/* ── User submitted feedbacks (shown first with NEW badge) ── */}
            {userFeedbacks.map((f, i) => (
              <div key={`user-${i}`} className="lp-fb" style={{
                ...CARD,
                border: '1px solid rgba(0,212,255,0.4)',
                background: 'rgba(0,212,255,0.04)',
                transition: 'border-color .2s',
                position: 'relative',
              }}>
                {/* NEW badge */}
                <div style={{
                  position: 'absolute', top: 12, right: 12,
                  background: '#00d4ff', color: '#0a0e1a',
                  fontSize: '.65rem', fontWeight: 800,
                  padding: '2px 8px', borderRadius: 20,
                  letterSpacing: '.06em',
                }}>NEW</div>

                <div style={{ color: '#f59e0b', marginBottom: '.75rem', fontSize: '1rem' }}>
                  {'★'.repeat(f.rating)}{'☆'.repeat(5 - f.rating)}
                </div>
                <p style={{ color: '#94a3b8', fontSize: '.9rem', lineHeight: 1.7, marginBottom: '1rem', fontStyle: 'italic' }}>
                  "{f.text}"
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: '50%',
                    background: 'linear-gradient(135deg,#00d4ff,#7c3aed)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: '.9rem', color: '#0a0e1a', flexShrink: 0,
                  }}>
                    {f.name ? f.name[0].toUpperCase() : '?'}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '.875rem' }}>{f.name}</div>
                    <div style={{ fontSize: '.75rem', color: '#64748b' }}>{f.role}</div>
                  </div>
                </div>
              </div>
            ))}

            {/* ── Original static testimonials ── */}
            {testimonials.map((t, i) => (
              <div key={`static-${i}`} className="lp-fb" style={{ ...CARD, transition: 'border-color .2s' }}>
                <div style={{ color: '#f59e0b', marginBottom: '.75rem', fontSize: '1rem' }}>
                  {'★'.repeat(t.s)}{'☆'.repeat(5 - t.s)}
                </div>
                <p style={{ color: '#94a3b8', fontSize: '.9rem', lineHeight: 1.7, marginBottom: '1rem', fontStyle: 'italic' }}>
                  {t.text}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: '50%',
                    background: 'linear-gradient(135deg,#00d4ff,#7c3aed)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: '.9rem', color: '#0a0e1a', flexShrink: 0,
                  }}>
                    {t.name[0]}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '.875rem' }}>{t.name}</div>
                    <div style={{ fontSize: '.75rem', color: '#64748b' }}>{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center', marginTop: '2.5rem' }}>
            <button className="lp-btn-out" style={BTN_OUT}
              onClick={() => setModal('feedback')}>
              💬 Submit Your Feedback
            </button>
          </div>
        </section>

        {/* ── CTA BAND ───────────────────────────────────────── */}
        <section style={{
          background: 'linear-gradient(135deg,rgba(0,212,255,.08),rgba(124,58,237,.08))',
          borderTop: '1px solid #2a3558', borderBottom: '1px solid #2a3558',
          padding: '4rem 2rem', textAlign: 'center',
        }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '.75rem' }}>
            Ready to Start Learning?
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '1.05rem', marginBottom: '2rem' }}>
            Join thousands of students learning coding in their own language.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="lp-btn-pri" style={{ ...BTN_PRI, ...BTN_LG }}
              onClick={() => setModal('register')}>
              🚀 Start for Free
            </button>
            <button className="lp-btn-out" style={{ ...BTN_OUT, ...BTN_LG }}
              onClick={() => setModal('login')}>
              Login
            </button>
          </div>
        </section>

        {/* ── FOOTER ─────────────────────────────────────────── */}
        <footer style={{
          background: '#0f1422', borderTop: '1px solid #2a3558',
          padding: '2.5rem 2rem', textAlign: 'center',
        }}>
          <div style={{ ...LOGO, justifyContent: 'center', marginBottom: '.5rem' }}>
            &lt;/&gt; <span style={{ color: '#e2e8f0' }}>CodeMentor</span>
          </div>
          <p style={{ color: '#64748b', fontSize: '.85rem', marginBottom: '1rem' }}>
            AI-Powered Programming Education
          </p>
          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
            {[
              { l: 'Features',         a: () => scrollTo('features')   },
              { l: 'How it Works',     a: () => scrollTo('howitworks') },
              { l: 'Submit Feedback',  a: () => setModal('feedback')   },
              { l: 'About',            a: () => scrollTo('about')      },
              { l: 'Register',         a: () => setModal('register')   },
              { l: 'Login',            a: () => setModal('login')      },
            ].map(x => (
              <button key={x.l} onClick={x.a} className="lp-footer-a"
                style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '.85rem', cursor: 'pointer', fontFamily: 'Sora,sans-serif', padding: 0, transition: 'color .2s' }}>
                {x.l}
              </button>
            ))}
          </div>
          <p style={{ color: '#334155', fontSize: '.78rem' }}>
            © 2025 CodeMentor — All rights reserved
          </p>
        </footer>
      </div>

      {/* ── MODALS ─────────────────────────────────────────────── */}
      {modal === 'login' && (
        <Modal onClose={close}>
          <LoginForm onLogin={onLogin} onSwitch={() => setModal('register')} onClose={close} />
        </Modal>
      )}
      {modal === 'register' && (
        <Modal onClose={close}>
          <RegisterForm onLogin={onLogin} onSwitch={() => setModal('login')} onClose={close} />
        </Modal>
      )}
      {modal === 'feedback' && (
        <Modal onClose={close}>
          <FeedbackForm
            onClose={close}
            onSubmit={(feedback) => {
              setUserFeedbacks(prev => [feedback, ...prev]);
            }}
          />
        </Modal>
      )}
    </>
  );
}