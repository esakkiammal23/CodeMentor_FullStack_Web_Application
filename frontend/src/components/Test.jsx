import React, { useState, useEffect, useRef, useCallback } from 'react';
import API from '../api';

const LANGUAGES = [
  { key: 'python', name: 'Python', icon: '🐍' },
  { key: 'java',   name: 'Java',   icon: '☕' },
  { key: 'ai',     name: 'AI',     icon: '🤖' },
  { key: 'ml',     name: 'ML',     icon: '📊' },
];

const IFACE_LANGS = [
  { key: 'english',   label: 'English'   },
  { key: 'tamil',     label: 'Tamil'     },
  { key: 'tanglish',  label: 'Tanglish'  },
  { key: 'hindi',     label: 'Hindi'     },
  { key: 'malayalam', label: 'Malayalam' },
];

const SECS    = 10;
const MAX_WARN = 3;

export default function Test({ user }) {
  const [lang, setLang]           = useState('python');
  const [iface, setIface]         = useState(user.preferred_language || 'english');
  const [phase, setPhase]         = useState('setup');
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ]   = useState(0);

  // answers stored as array parallel to questions: answers[i] = selected option string or ''
  const [answers, setAnswers]     = useState([]);

  const [timeLeft, setTimeLeft]   = useState(SECS);
  const [result, setResult]       = useState(null);
  const [certMsg, setCertMsg]     = useState('');
  const [certLoading, setCertLoading] = useState(false);
  const [error, setError]         = useState('');
  const [tabWarn, setTabWarn]     = useState(0);
  const timerRef = useRef(null);

  // Tab detection
  useEffect(() => {
    if (phase !== 'test') return;
    const bump = () => setTabWarn(p => {
      const n = p + 1;
      if (n >= MAX_WARN) setPhase('terminated');
      return n;
    });
    const onVis  = () => { if (document.hidden) bump(); };
    document.addEventListener('visibilitychange', onVis);
    window.addEventListener('blur', bump);
    return () => {
      document.removeEventListener('visibilitychange', onVis);
      window.removeEventListener('blur', bump);
    };
  }, [phase]);

  // Block right-click/copy during test
  useEffect(() => {
    if (phase !== 'test') return;
    const block = e => e.preventDefault();
    document.addEventListener('contextmenu', block);
    document.addEventListener('copy', block);
    return () => {
      document.removeEventListener('contextmenu', block);
      document.removeEventListener('copy', block);
    };
  }, [phase]);

  // Build answers object from array for submission
  // key = question index (0-based), value = selected option
  // We send the full questions array + answers array so backend can zip them
  const buildSubmitPayload = useCallback((qs, ans) => {
    // Build a simple parallel structure: for each question, what did user pick?
    return qs.map((q, i) => ({
      question_index: i,
      question_id: q.id,
      selected: ans[i] || '',
      correct: q.correct,
      question: q.question,
      explanation: q.explanation || '',
    }));
  }, []);

  const doSubmit = useCallback(async (qs, ans) => {
    clearInterval(timerRef.current);
    setPhase('submitting');

    const payload = buildSubmitPayload(qs, ans);

    try {
      const res = await API.post('/tests/course/submit/', {
        language: lang,
        interface_language: iface,
        // Send the paired data — backend just needs to count correct ones
        paired: payload,
        // Also send legacy format as fallback
        answers: Object.fromEntries(qs.map((q, i) => [String(i + 1), ans[i] || ''])),
        questions: qs,
      });
      setResult(res.data);
      setPhase('result');
    } catch (e) {
      setError('Submit failed. Please try again.');
      setPhase('setup');
    }
  }, [lang, iface, buildSubmitPayload]);

  const goNext = useCallback((qs, ans) => {
    setCurrentQ(prev => {
      const next = prev + 1;
      if (next >= qs.length) {
        doSubmit(qs, ans);
        return prev;
      }
      setTimeLeft(SECS);
      return next;
    });
  }, [doSubmit]);

  // Timer
  useEffect(() => {
    if (phase !== 'test') return;
    clearInterval(timerRef.current);
    setTimeLeft(SECS);
    timerRef.current = setInterval(() => {
      setTimeLeft(p => {
        if (p <= 1) {
          clearInterval(timerRef.current);
          setAnswers(ans => {
            setQuestions(qs => {
              goNext(qs, ans);
              return qs;
            });
            return ans;
          });
          return SECS;
        }
        return p - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [phase, currentQ]); // eslint-disable-line

  const startTest = async () => {
    setPhase('loading'); setError('');
    try {
      const res = await API.get(
        `/tests/course/generate/?language=${lang}&interface_language=${iface}`
      );
      const qs = res.data.questions;
      setQuestions(qs);
      setAnswers(new Array(qs.length).fill(''));
      setCurrentQ(0);
      setTabWarn(0);
      setTimeLeft(SECS);
      setPhase('test');
    } catch (e) {
      const d = e.response?.data;
      setError(d?.locked ? `🔒 ${d.error}` : d?.error || 'Failed to load. Try again.');
      setPhase('setup');
    }
  };

  const selectAnswer = (opt) => {
    if (answers[currentQ]) return; // already answered
    const updated = [...answers];
    updated[currentQ] = opt;
    setAnswers(updated);
    clearInterval(timerRef.current);
    setTimeout(() => goNext(questions, updated), 350);
  };

  const tc = timeLeft <= 3 ? '#ef4444' : timeLeft <= 6 ? '#f59e0b' : '#34d399';

  // ── TERMINATED ─────────────────────────────────────────────────
  if (phase === 'terminated') return (
    <div className="card text-center">
      <p style={{ fontSize: '3rem', marginBottom: 12 }}>🚫</p>
      <h2 style={{ color: '#ef4444', marginBottom: 10 }}>Test Terminated</h2>
      <p className="text-muted" style={{ marginBottom: 20 }}>
        You switched tabs {MAX_WARN} times.
      </p>
      <button className="btn btn-outline"
        onClick={() => { setPhase('setup'); setTabWarn(0); }}>
        Try Again
      </button>
    </div>
  );

  // ── LOADING / SUBMITTING ────────────────────────────────────────
  if (phase === 'loading' || phase === 'submitting') return (
    <div className="card text-center">
      <div className="spinner" />
      <p className="text-muted">
        {phase === 'loading' ? 'Loading questions…' : 'Submitting your answers…'}
      </p>
    </div>
  );

  // ── RESULT ─────────────────────────────────────────────────────
  if (phase === 'result' && result) return (
    <div>
      <div className="card text-center">
        <div className={`score-circle ${result.passed ? 'score-pass' : 'score-fail'}`}>
          <span>{result.score}</span>
          <span style={{ fontSize: '1rem' }}>/20</span>
        </div>
        <h2 style={{ color: result.passed ? '#34d399' : '#f87171', marginBottom: 10 }}>
          {result.passed ? '🎉 Course Completed!' : '😔 Not Passed Yet'}
        </h2>
        <p className="text-muted">{result.message}</p>

        {result.passed && (
          <div style={{ marginTop: 20 }}>
            {result.cert_generated && result.pdf_url && (
              <div style={{ marginBottom: 12 }}>
                
              <a
  href={`https://codementor-fullstack-web-application.onrender.com${result.pdf_url}`}
                  target="_blank" rel="noreferrer"
                  className="btn btn-success"
                  style={{ display: 'inline-block' }}
                >
                  📄 Download Certificate
                </a>
              </div>
            )}
            {result.email_sent && (
              <p style={{ color: '#6ee7b7', fontSize: '0.85rem' }}>
                ✉️ Certificate sent to your registered email!
              </p>
            )}
            {certMsg && (
              <div className="alert alert-success" style={{ marginTop: 14 }}>{certMsg}</div>
            )}
          </div>
        )}

        <button className="btn btn-outline" style={{ marginTop: 14 }}
          onClick={() => { setPhase('setup'); setResult(null); setCertMsg(''); }}>
          Try Again
        </button>
      </div>

      <h3 style={{ color: '#a78bfa', margin: '20px 0 14px' }}>📋 Answer Review</h3>
      {result.results.map((r, i) => (
        <div key={i} className="question-card">
          <p className="question-text">{i + 1}. {r.question}</p>
          <p style={{ fontSize: '0.85rem', color: r.is_correct ? '#6ee7b7' : '#f87171' }}>
            {r.is_correct ? '✓' : '✗'} Your answer: {r.your_answer || '(skipped — time expired)'}
          </p>
          {!r.is_correct && (
            <p style={{ fontSize: '0.85rem', color: '#6ee7b7' }}>✓ Correct: {r.correct_answer}</p>
          )}
          {r.explanation && (
            <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: 4 }}>💡 {r.explanation}</p>
          )}
        </div>
      ))}
    </div>
  );

  // ── ACTIVE TEST ────────────────────────────────────────────────
  if (phase === 'test' && questions.length > 0) {
    const q        = questions[currentQ];
    const progress = (currentQ / questions.length) * 100;
    const answered = answers[currentQ];

    return (
      <div>
        {tabWarn > 0 && (
          <div className="alert alert-error" style={{ marginBottom: 12 }}>
            ⚠️ Tab warning {tabWarn}/{MAX_WARN}
            {tabWarn === MAX_WARN - 1 && ' — one more will terminate the test!'}
          </div>
        )}

        <div className="card" style={{ padding: '12px 18px', marginBottom: 12 }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', flexWrap: 'wrap', gap: 8,
          }}>
            <span style={{ color: '#a78bfa', fontWeight: 600 }}>
              📝 {lang.toUpperCase()} Course Test
            </span>
            <span className="text-muted" style={{ fontSize: '0.82rem' }}>
              Q{currentQ + 1} of {questions.length} &nbsp;|&nbsp; Pass: 17/20
            </span>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'rgba(0,0,0,0.3)', padding: '5px 12px',
              borderRadius: 20, border: `2px solid ${tc}`,
            }}>
              <span style={{ color: tc, fontWeight: 700, fontSize: '1.1rem' }}>{timeLeft}s</span>
            </div>
          </div>
          <div className="progress-bar-wrap" style={{ marginTop: 8, height: 5 }}>
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <div className="question-card">
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'flex-start', marginBottom: 14,
          }}>
            <p className="question-text" style={{ margin: 0, flex: 1 }}>
              Q{currentQ + 1}. {q?.question}
            </p>
            <div style={{
              minWidth: 40, height: 40, borderRadius: '50%',
              border: `3px solid ${tc}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginLeft: 10, color: tc, fontWeight: 700,
              fontSize: '0.85rem', flexShrink: 0,
            }}>
              {timeLeft}
            </div>
          </div>

          {q?.options.map(opt => (
            <button
              key={opt}
              className={`option-btn ${answered === opt ? 'selected' : ''}`}
              onClick={() => selectAnswer(opt)}
              disabled={!!answered}
            >
              {opt}
            </button>
          ))}
        </div>

        <div style={{
          display: 'flex', gap: 10, alignItems: 'center',
          marginBottom: 30, flexWrap: 'wrap',
        }}>
          <button className="btn btn-outline"
            onClick={() => goNext(questions, answers)}
            style={{ fontSize: '0.85rem' }}>
            Skip →
          </button>
          <span className="text-muted" style={{ fontSize: '0.8rem' }}>
            Answered: {answers.filter(a => a !== '').length}/{questions.length}
          </span>
          <button className="btn btn-danger"
            onClick={() => doSubmit(questions, answers)}
            style={{ marginLeft: 'auto', fontSize: '0.85rem' }}>
            Submit Now
          </button>
        </div>
      </div>
    );
  }

  // ── SETUP ──────────────────────────────────────────────────────
  return (
    <div>
      <div className="card">
        <h2 className="card-title">📝 Course Completion Test</h2>
        <p className="text-muted" style={{ marginBottom: 20 }}>
          Pass all topic tests first. Then take this 20-question final test.
          Score <strong>17/20</strong> to earn your certificate.
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="form-group">
          <label className="form-label">Programming Language</label>
          <div className="lang-grid">
            {LANGUAGES.map(l => (
              <div key={l.key}
                className={`lang-card ${lang === l.key ? 'selected' : ''}`}
                onClick={() => setLang(l.key)}>
                <div className="lang-icon">{l.icon}</div>
                <div className="lang-name">{l.name}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Question Language</label>
          <select className="form-select" value={iface}
            onChange={e => setIface(e.target.value)}>
            {IFACE_LANGS.map(l => (
              <option key={l.key} value={l.key}>{l.label}</option>
            ))}
          </select>
        </div>

        <div className="alert alert-info" style={{ marginBottom: 16 }}>
          <strong>Rules:</strong><br />
          ⏱ 10 seconds per question — auto-skips on timeout<br />
          🔒 All topic tests must be passed to unlock this test<br />
          🚫 Tab switching detected — {MAX_WARN} warnings = terminated<br />
          🏆 Score 17/20 or above → certificate sent to your email
        </div>

        <button className="btn btn-primary" onClick={startTest}>
          🚀 Start {lang.toUpperCase()} Final Test
        </button>
      </div>
    </div>
  );
}