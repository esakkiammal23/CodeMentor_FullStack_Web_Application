import React, { useState, useEffect, useRef, useCallback } from 'react';
import API from '../api';
import CodeEditor from './CodeEditor';

const LANGUAGES = [
  { key: 'python', name: 'Python',                  icon: '🐍' },
  { key: 'java',   name: 'Java',                    icon: '☕' },
  { key: 'ai',     name: 'Artificial Intelligence', icon: '🤖' },
  { key: 'ml',     name: 'Machine Learning',        icon: '📊' },
];

const IFACE_LANGS = [
  { key: 'english',   label: 'English'   },
  { key: 'tamil',     label: 'Tamil'     },
  { key: 'tanglish',  label: 'Tanglish'  },
  { key: 'hindi',     label: 'Hindi'     },
  { key: 'malayalam', label: 'Malayalam' },
];

const TOPIC_TIMER = 10;
const MAX_WARN    = 3;

/* ─── tiny helpers ─────────────────────────────────────────── */
const scrollStyle = {
  overflowY: 'auto',
  scrollbarWidth: 'thin',
  scrollbarColor: 'rgba(124,58,237,0.4) transparent',
};

/* ═══════════════════════════════════════════════════════════════
   TOPIC TEST MODAL  (unchanged logic, same as before)
═══════════════════════════════════════════════════════════════ */
function TopicTestModal({ topic, ifaceLang, onClose, onPassed, onWeak }) {
  const [phase, setPhase]         = useState('loading');
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ]   = useState(0);
  const [answers, setAnswers]     = useState({});
  const [timeLeft, setTimeLeft]   = useState(TOPIC_TIMER);
  const [result, setResult]       = useState(null);
  const [tabWarn, setTabWarn]     = useState(0);
  const timerRef = useRef(null);

  useEffect(() => {
    API.get(`/tests/topic/generate/?topic_id=${topic.id}&interface_language=${ifaceLang}`)
      .then(r => { setQuestions(r.data.questions); setPhase('test'); })
      .catch(() => setPhase('error'));
  }, [topic.id, ifaceLang]);

  useEffect(() => {
    if (phase !== 'test') return;
    const warn = () => setTabWarn(p => { const n = p + 1; if (n >= MAX_WARN) setPhase('terminated'); return n; });
    const onVis  = () => { if (document.hidden) warn(); };
    document.addEventListener('visibilitychange', onVis);
    window.addEventListener('blur', warn);
    return () => { document.removeEventListener('visibilitychange', onVis); window.removeEventListener('blur', warn); };
  }, [phase]);

  useEffect(() => {
    if (phase !== 'test') return;
    const block = e => e.preventDefault();
    document.addEventListener('contextmenu', block);
    document.addEventListener('copy', block);
    return () => { document.removeEventListener('contextmenu', block); document.removeEventListener('copy', block); };
  }, [phase]);

  const doSubmit = useCallback(async (ans) => {
    clearInterval(timerRef.current);
    setPhase('submitting');
    try {
      const res = await API.post('/tests/topic/submit/', {
        topic_id: topic.id, answers: ans, questions, interface_language: ifaceLang,
      });
      setResult(res.data);
      setPhase('result');
      if (res.data.passed) {onPassed(topic);}
      else {onWeak(topic, res.data.score);
}
    } catch { setPhase('error'); }
  }, [questions, topic, ifaceLang, onPassed, onWeak]);

  const goNext = useCallback((ans) => {
    setCurrentQ(prev => {
      const next = prev + 1;
      if (next >= questions.length) { doSubmit(ans); return prev; }
      setTimeLeft(TOPIC_TIMER);
      return next;
    });
  }, [questions.length, doSubmit]);

  useEffect(() => {
    if (phase !== 'test') return;
    clearInterval(timerRef.current);
    setTimeLeft(TOPIC_TIMER);
    timerRef.current = setInterval(() => {
      setTimeLeft(p => {
        if (p <= 1) { clearInterval(timerRef.current); setAnswers(a => { goNext(a); return a; }); return TOPIC_TIMER; }
        return p - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [phase, currentQ]); // eslint-disable-line

  const selectAnswer = opt => {
    const qid = questions[currentQ]?.id;
    if (!qid || answers[qid]) return;
    const updated = { ...answers, [qid]: opt };
    setAnswers(updated);
    clearInterval(timerRef.current);
    setTimeout(() => goNext(updated), 350);
  };

  const tc = timeLeft <= 3 ? '#ef4444' : timeLeft <= 6 ? '#f59e0b' : '#34d399';

  const overlay = (children) => (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      zIndex: 2000, padding: 20,
    }}>
      <div style={{
        background: '#1a1535', borderRadius: 20, padding: 32,
        width: '100%', maxWidth: 660, maxHeight: '90vh',
        overflowY: 'auto', border: '1px solid rgba(124,58,237,0.3)',
      }}>
        {children}
      </div>
    </div>
  );

  if (phase === 'loading' || phase === 'submitting') return overlay(
    <div style={{ textAlign: 'center' }}>
      <div className="spinner" />
      <p className="text-muted">{phase === 'loading' ? 'Loading questions…' : 'Submitting…'}</p>
    </div>
  );

  if (phase === 'error') return overlay(
    <div style={{ textAlign: 'center' }}>
      <p style={{ color: '#ef4444', marginBottom: 12 }}>❌ Failed to load test.</p>
      <button className="btn btn-outline" onClick={onClose}>Close</button>
    </div>
  );

  if (phase === 'terminated') return overlay(
    <div style={{ textAlign: 'center' }}>
      <p style={{ fontSize: '2.5rem', marginBottom: 8 }}>🚫</p>
      <h3 style={{ color: '#ef4444', marginBottom: 8 }}>Test Terminated</h3>
      <p className="text-muted" style={{ marginBottom: 16 }}>You switched tabs {MAX_WARN} times.</p>
      <button className="btn btn-outline" onClick={onClose}>Close</button>
    </div>
  );

  if (phase === 'result' && result) return overlay(
    <div>
      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <div className={`score-circle ${result.passed ? 'score-pass' : 'score-fail'}`}
          style={{ width: 110, height: 110, fontSize: '2rem', margin: '0 auto 14px' }}>
          <span>{result.score}</span><span style={{ fontSize: '0.9rem' }}>/10</span>
        </div>
        <h3 style={{ color: result.passed ? '#34d399' : '#f87171', marginBottom: 8 }}>
          {result.passed ? '✅ Topic Passed! Next topic unlocked.' : '🔴 Weak Topic Detected'}
        </h3>
        <p style={{
          color: result.passed ? '#9ca3af' : '#fca5a5',
          fontSize: '0.9rem',
          lineHeight: 1.6,
        }}>
          {result.message}
        </p>

        {/* Weak topic warning block */}
        {!result.passed && (
          <div style={{
            marginTop: 16, padding: '14px 18px',
            background: 'rgba(220,38,38,0.12)',
            border: '1px solid rgba(220,38,38,0.35)',
            borderRadius: 12, textAlign: 'left',
          }}>
            <p style={{ color: '#fca5a5', fontWeight: 700, marginBottom: 6, fontSize: '0.92rem' }}>
              ⚠️ You need more focus on this topic!
            </p>
            <p style={{ color: '#f87171', fontSize: '0.82rem', lineHeight: 1.7 }}>
              • You scored <strong>{result.score}/10</strong> — you need <strong>7/10</strong> to pass<br />
              • This topic is marked as <strong>weak</strong> for you<br />
              • Re-read the lesson carefully using the left panel<br />
              • Ask the AI tutor your doubts using the right panel<br />
              • Then retry the test — you <strong>must pass</strong> to move to the next topic
            </p>
          </div>
        )}
      </div>

      <h4 style={{ color: '#a78bfa', marginBottom: 10, fontSize: '0.95rem' }}>📋 Answer Review</h4>
      {result.results.map((r, i) => (
        <div key={i} style={{
          padding: '10px 12px', marginBottom: 8, borderRadius: 8,
          background: r.is_correct ? 'rgba(5,150,105,0.1)' : 'rgba(220,38,38,0.1)',
          border: `1px solid ${r.is_correct ? 'rgba(5,150,105,0.3)' : 'rgba(220,38,38,0.3)'}`,
        }}>
          <p style={{ fontSize: '0.85rem', color: '#e2e8f0', marginBottom: 4 }}>{i + 1}. {r.question}</p>
          <p style={{ fontSize: '0.78rem', color: r.is_correct ? '#6ee7b7' : '#f87171' }}>
            {r.is_correct ? '✓' : '✗'} {r.your_answer || '(skipped — time expired)'}
          </p>
          {!r.is_correct && <p style={{ fontSize: '0.78rem', color: '#6ee7b7' }}>✓ Correct: {r.correct_answer}</p>}
          {r.explanation && <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: 4 }}>💡 {r.explanation}</p>}
        </div>
      ))}

      <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
        {!result.passed && (
          <>
            <button className="btn btn-primary" onClick={() => {
              setPhase('loading'); setAnswers({}); setCurrentQ(0); setResult(null);
              API.get(`/tests/topic/generate/?topic_id=${topic.id}&interface_language=${ifaceLang}`)
                .then(r => { setQuestions(r.data.questions); setPhase('test'); })
                .catch(() => setPhase('error'));
            }}>🔄 Retry Test</button>
            <button className="btn btn-outline" onClick={onClose}
              style={{ color: '#c4b5fd', borderColor: 'rgba(124,58,237,0.5)' }}>
              📖 Go Back & Revise
            </button>
          </>
        )}
        {result.passed && (
          <button className="btn btn-outline" onClick={onClose}>✅ Continue</button>
        )}
      </div>
    </div>
  );

  if (phase === 'test' && questions.length > 0) {
    const q = questions[currentQ];
    return overlay(
      <div>
        {tabWarn > 0 && (
          <div className="alert alert-error" style={{ marginBottom: 10, fontSize: '0.82rem' }}>
            ⚠️ Tab warning {tabWarn}/{MAX_WARN}
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div>
            <p style={{ color: '#a78bfa', fontWeight: 600, fontSize: '0.95rem' }}>📝 {topic.name}</p>
            <p style={{ color: '#9ca3af', fontSize: '0.78rem' }}>Q{currentQ + 1}/{questions.length} &nbsp;|&nbsp; Pass: 7/10</p>
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(0,0,0,0.35)', padding: '6px 14px',
            borderRadius: 20, border: `2px solid ${tc}`,
          }}>
            <span style={{ color: tc, fontWeight: 700, fontSize: '1.2rem' }}>{timeLeft}s</span>
          </div>
        </div>
        <div className="progress-bar-wrap" style={{ height: 5, marginBottom: 16 }}>
          <div className="progress-bar-fill" style={{ width: `${(currentQ / questions.length) * 100}%` }} />
        </div>
        <p className="question-text" style={{ marginBottom: 14 }}>Q{currentQ + 1}. {q?.question}</p>
        {q?.options.map(opt => (
          <button key={opt} className={`option-btn ${answers[q.id] === opt ? 'selected' : ''}`}
            onClick={() => selectAnswer(opt)} disabled={!!answers[q.id]}>{opt}</button>
        ))}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12 }}>
          <button className="btn btn-outline" style={{ fontSize: '0.82rem', padding: '7px 16px' }}
            onClick={() => { clearInterval(timerRef.current); goNext(answers); }}>Skip →</button>
          <button className="btn btn-danger" style={{ fontSize: '0.82rem', padding: '7px 16px' }}
            onClick={() => doSubmit(answers)}>Submit Now</button>
        </div>
      </div>
    );
  }
  return null;
}

/* ═══════════════════════════════════════════════════════════════
   LEADERBOARD MODAL
═══════════════════════════════════════════════════════════════ */
function LeaderboardModal({ lang, onClose }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const NAMES = { python: 'Python', java: 'Java', ai: 'AI', ml: 'ML' };

  useEffect(() => {
    API.get(`/tests/leaderboard/?language=${lang}`)
      .then(r => setData(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, [lang]);

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      zIndex: 2000, padding: 20,
    }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{
        background: '#1a1535', borderRadius: 20, padding: 28,
        width: '100%', maxWidth: 520, maxHeight: '85vh',
        overflowY: 'auto', border: '1px solid  #00d4ff;',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ color: '#00d4ff', fontWeight: 700, margin: 0 }}>🏆 {NAMES[lang]} Leaderboard</h3>
          <button className="btn btn-outline" style={{ padding: '5px 12px' }} onClick={onClose}>✕</button>
        </div>
        {loading ? <div className="spinner" /> : !data?.leaderboard?.length ? (
          <p className="text-muted" style={{ textAlign: 'center' }}>No entries yet!</p>
        ) : (
          <>
            {data.my_rank && (
              <div className="alert alert-info" style={{ marginBottom: 12, fontSize: '0.85rem' }}>
                Your rank: <strong>#{data.my_rank}</strong>
              </div>
            )}
            {data.leaderboard.map(e => (
              <div key={e.rank} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 14px', borderRadius: 10, marginBottom: 8,
                background: e.is_me ? 'rgba(124,58,237,0.2)' : 'rgba(255,255,255,0.05)',
                border: e.is_me ? '1px solid rgba(124,58,237,0.5)' : '1px solid rgba(255,255,255,0.08)',
              }}>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', minWidth: 32, textAlign: 'center',
                  color: e.rank === 1 ? '#fbbf24' : e.rank === 2 ? '#9ca3af' : e.rank === 3 ? '#b45309' : '#8b4300' }}>
                  {e.rank === 1 ? '🥇' : e.rank === 2 ? '🥈' : e.rank === 3 ? '🥉' : `#${e.rank}`}
                </span>
                <div style={{ flex: 1 }}>
                  <p style={{ fontWeight: 600, color: e.is_me ? '#fff' : '#e2e8f0', fontSize: '0.9rem', marginBottom: 2 }}>
                    {e.username} {e.is_me && <span style={{ fontSize: '0.75rem', color: ' --accent: #00d4ff' }}>(You)</span>}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Topics passed: {e.topics_completed}</p>
                </div>
                <span style={{ fontWeight: 700, color: '#34d399', fontSize: '1rem' }}>{e.total_score} pts</span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   TWO-PANEL LESSON MODAL
   Left  — lesson content with scroll
   Right — AI doubt chatbot with scroll + input
═══════════════════════════════════════════════════════════════ */
function LessonModal({ topic, ifaceLang, topicStatus, onClose, onTestClick }) {
  const [activeTab, setActiveTab] = useState(topic._openDoubtTab ? 'doubt' : 'learn');
  const [content, setContent]         = useState('');
  const [loading, setLoading]         = useState(true);
  const [hasScrolled, setHasScrolled] = useState(false);
  const [chatMsgs, setChatMsgs]       = useState([{
    role: 'bot',
    text: `Hi! 👋 I'm your AI tutor for "${topic.name}".\n\nRead the lesson on the left, then come here to ask me anything about this topic!`,
  }]);
  const [doubt, setDoubt]             = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const contentRef = useRef(null);
  const chatEnd    = useRef(null);
  const inputRef   = useRef(null);

  useEffect(() => {
    setLoading(true);
    setHasScrolled(false);
    API.post('/courses/learn/', { topic_id: topic.id, interface_language: ifaceLang })
      .then(r => setContent(r.data.content))
      .catch(() => setContent('Failed to load. Please try again.'))
      .finally(() => setLoading(false));

    setChatMsgs([{
      role: 'bot',
      text: topic._openDoubtTab
        ? `⚠️ You scored less than 7/10 on "${topic.name}".\n\nDon't worry! Let me help you understand this topic better. What part was confusing? Ask me anything and I'll explain it clearly! 💪`
        : `Hi! 👋 I'm your AI tutor for "${topic.name}".\n\nRead the lesson on the left, then come here to ask me anything about this topic!`,
    }]);
  }, [topic.id, ifaceLang]); // eslint-disable-line

  
  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMsgs]);

  // When switching to doubt tab, focus input
  useEffect(() => {
    if (activeTab === 'doubt') setTimeout(() => inputRef.current?.focus(), 100);
  }, [activeTab]);

  const handleScroll = () => {
    const el = contentRef.current;
    if (el && el.scrollTop + el.clientHeight >= el.scrollHeight - 30) setHasScrolled(true);
  };

  const sendDoubt = async () => {
    const q = doubt.trim();
    if (!q || chatLoading) return;
    setDoubt('');
    setChatMsgs(p => [...p, { role: 'user', text: q }]);
    setChatLoading(true);
    try {
      const res = await API.post('/courses/doubt/', {
        topic_id: topic.id, question: q, interface_language: ifaceLang,
      });
      setChatMsgs(p => [...p, { role: 'bot', text: res.data.answer }]);
    } catch {
      setChatMsgs(p => [...p, { role: 'bot', text: 'Sorry, could not process. Please try again.' }]);
    }
    setChatLoading(false);
  };

  const testPassed = topicStatus?.passed;

  // ── shared panel height ────────────────────────────────────────
  const PANEL_H = 'calc(90vh - 160px)'; // viewport minus header+footer

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.82)',
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      zIndex: 1500, padding: '16px',
    }}>
      <div style={{
        width: '100%', maxWidth: 1100,
        height: '90vh',
        background: 'linear-gradient(145deg, #1e1a3a, #16122e)',
        borderRadius: 20,
        border: '1px solid rgba(124,58,237,0.35)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
      }}>

        {/* ── TOP BAR ────────────────────────────────────────────── */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 22px',
          background: 'rgba(124,58,237,0.12)',
          borderBottom: '1px solid rgba(124,58,237,0.2)',
          flexShrink: 0,
        }}>
          {/* Title */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: 'rgba(124,58,237,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.2rem',
            }}>📘</div>
            <div>
              <p style={{ color: '#e9d5ff', fontWeight: 700, fontSize: '1.05rem', lineHeight: 1.2 }}>
                {topic.name}
              </p>
              <p style={{ color: '#9ca3af', fontSize: '0.75rem' }}>
                {LANGUAGES.find(l => l.key === topic.programming_language)?.name || topic.programming_language}
                &nbsp;·&nbsp;{ifaceLang.charAt(0).toUpperCase() + ifaceLang.slice(1)}
              </p>
            </div>
          </div>

          {/* Tab switcher — pill style */}
          <div style={{
            display: 'flex', background: 'rgba(0,0,0,0.3)',
            borderRadius: 12, padding: 4, gap: 4,
          }}>
            {[
              { key: 'learn', icon: '📖', label: 'Learn' },
              { key: 'doubt', icon: '💬', label: 'Ask Doubt' },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  padding: '7px 18px', borderRadius: 9, border: 'none', cursor: 'pointer',
                  fontWeight: 600, fontSize: '0.88rem', transition: 'all 0.2s',
                  background: activeTab === tab.key
                    ? 'linear-gradient(135deg, #7c3aed, #6d28d9)'
                    : 'transparent',
                  color: activeTab === tab.key ? '#fff' : '#9ca3af',
                  boxShadow: activeTab === tab.key ? '0 2px 10px rgba(124,58,237,0.5)' : 'none',
                }}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>

          {/* Right actions */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {testPassed && (
              <span style={{
                padding: '5px 12px', borderRadius: 20,
                background: 'rgba(5,150,105,0.2)', border: '1px solid rgba(5,150,105,0.4)',
                color: '#6ee7b7', fontSize: '0.78rem', fontWeight: 600,
              }}>
                ✓ {topicStatus.best_score}/10
              </span>
            )}
            <button className="btn btn-outline" style={{ padding: '6px 14px', fontSize: '0.85rem' }}
              onClick={onClose}>✕ Close</button>
          </div>
        </div>

        {/* ── BODY: two panels side by side ──────────────────────── */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

          {/* ── LEFT PANEL — Lesson ─────────────────────────────── */}
          <div style={{
            flex: 1,
            display: 'flex', flexDirection: 'column',
            borderRight: '1px solid rgba(255,255,255,0.08)',
            // On mobile show only active tab
            ...(activeTab === 'doubt' ? { display: 'none' } : {}),
          }}
            className="learn-panel"
          >
            {/* Panel header */}
            <div style={{
              padding: '12px 20px',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              flexShrink: 0,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: '1.1rem' }}>📖</span>
                <span style={{ color: '#c4b5fd', fontWeight: 600, fontSize: '0.92rem' }}>Lesson</span>
                {loading && <span style={{ color: '#9ca3af', fontSize: '0.78rem' }}>Loading…</span>}
              </div>
              {!loading && !hasScrolled && (
                <span style={{
                  fontSize: '0.72rem', color: '#7c3aed',
                  background: 'rgba(124,58,237,0.15)',
                  padding: '3px 10px', borderRadius: 20,
                  border: '1px solid rgba(124,58,237,0.3)',
                  animation: 'pulse 2s infinite',
                }}>
                  ⬇ Scroll to unlock test
                </span>
              )}
              {hasScrolled && !testPassed && (
                <button
                  className="btn btn-success"
                  style={{ padding: '6px 14px', fontSize: '0.82rem' }}
                  onClick={onTestClick}
                >
                  📝 Take Test
                </button>
              )}
              {testPassed && (
                <button
                  className="btn btn-outline"
                  style={{ padding: '6px 14px', fontSize: '0.82rem', color: '#6ee7b7', borderColor: '#059669' }}
                  onClick={onTestClick}
                >
                  🔄 Retake Test
                </button>
              )}
            </div>

            {/* Lesson body — scrollable */}
            <div
              ref={contentRef}
              onScroll={handleScroll}
              style={{
                flex: 1, padding: '20px 24px',
                ...scrollStyle,
              }}
            >
              {loading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 60 }}>
                  <div className="spinner" />
                  <p style={{ color: '#9ca3af', marginTop: 12 }}>Preparing your lesson…</p>
                </div>
              ) : (
                <>
                  <div style={{
                    whiteSpace: 'pre-wrap', lineHeight: 1.85,
                    color: '#e2e8f0', fontSize: '0.95rem',
                    fontFamily: 'inherit',
                  }}>
                    {content}
                  </div>

                  {/* Bottom CTA after reading */}
                  <div style={{
                    marginTop: 28, padding: '16px 18px',
                    background: hasScrolled
                      ? 'rgba(5,150,105,0.12)' : 'rgba(124,58,237,0.08)',
                    borderRadius: 12,
                    border: hasScrolled
                      ? '1px solid rgba(5,150,105,0.3)' : '1px solid rgba(124,58,237,0.2)',
                  }}>
                    {hasScrolled ? (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                        <div>
                          <p style={{ color: '#6ee7b7', fontWeight: 600, marginBottom: 2, fontSize: '0.9rem' }}>
                            ✅ Lesson complete!
                          </p>
                          <p style={{ color: '#9ca3af', fontSize: '0.78rem' }}>
                            {testPassed
                              ? `You already passed this topic (${topicStatus.best_score}/10). You can retake the test.`
                              : 'Now take the topic test — score 7/10 to unlock the next topic.'}
                          </p>
                        </div>
                        <button
                          className="btn btn-success"
                          style={{ padding: '8px 20px', fontSize: '0.88rem' }}
                          onClick={onTestClick}
                        >
                          {testPassed ? '🔄 Retake Test' : '📝 Take Topic Test →'}
                        </button>
                      </div>
                    ) : (
                      <p style={{ color: '#9ca3af', fontSize: '0.82rem', textAlign: 'center' }}>
                        ⬇ Keep reading… the test button unlocks when you reach the bottom
                      </p>
                    )}
                  </div>

                  {/* Reload */}
                  <div style={{ marginTop: 14, textAlign: 'center' }}>
                    <button
                      className="btn btn-outline"
                      style={{ fontSize: '0.8rem', padding: '6px 16px', color: '#9ca3af' }}
                      onClick={() => {
                        setLoading(true); setHasScrolled(false);
                        API.post('/courses/learn/', { topic_id: topic.id, interface_language: ifaceLang })
                          .then(r => setContent(r.data.content))
                          .catch(() => setContent('Failed.'))
                          .finally(() => setLoading(false));
                      }}
                    >
                      🔄 Reload Lesson
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ── RIGHT PANEL — Chatbot ───────────────────────────── */}
          <div style={{
            width: 400, minWidth: 340,
            display: 'flex', flexDirection: 'column',
            background: 'rgba(0,0,0,0.15)',
            ...(activeTab === 'learn' ? {} : { flex: 1, width: 'auto' }),
          }}
            className="doubt-panel"
          >
            {/* Panel header */}
            <div style={{
              padding: '12px 18px',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0,
            }}>
              <div style={{
                width: 34, height: 34, borderRadius: 10,
                background: 'linear-gradient(135deg,#7c3aed,#4f46e5)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1rem', flexShrink: 0,
              }}>🤖</div>
              <div>
                <p style={{ color: '#c4b5fd', fontWeight: 600, fontSize: '0.92rem', lineHeight: 1.2 }}>AI Tutor</p>
                <p style={{ color: '#6b7280', fontSize: '0.7rem' }}>Ask anything about {topic.name}</p>
              </div>
              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#34d399' }} />
                <span style={{ color: '#34d399', fontSize: '0.7rem' }}>Online</span>
              </div>
            </div>

            {/* Messages — scrollable */}
            <div style={{
              flex: 1,
              padding: '16px 14px',
              display: 'flex', flexDirection: 'column', gap: 12,
              ...scrollStyle,
            }}>
              {chatMsgs.map((m, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
                  gap: 8, alignItems: 'flex-end',
                }}>
                  {/* Bot avatar */}
                  {m.role === 'bot' && (
                    <div style={{
                      width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                      background: 'linear-gradient(135deg,#7c3aed,#4f46e5)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.75rem', marginBottom: 2,
                    }}>🤖</div>
                  )}

                  <div style={{
                    maxWidth: '80%',
                    padding: '10px 14px',
                    borderRadius: m.role === 'user'
                      ? '16px 16px 4px 16px'
                      : '16px 16px 16px 4px',
                    background: m.role === 'user'
                      ? 'linear-gradient(135deg, #7c3aed, #6d28d9)'
                      : 'rgba(255,255,255,0.07)',
                    border: m.role === 'user'
                      ? 'none'
                      : '1px solid rgba(255,255,255,0.1)',
                    fontSize: '0.87rem',
                    lineHeight: 1.65,
                    color: '#e2e8f0',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    boxShadow: m.role === 'user'
                      ? '0 2px 12px rgba(124,58,237,0.35)'
                      : 'none',
                  }}>
                    {m.text}
                  </div>

                  {/* User avatar */}
                  {m.role === 'user' && (
                    <div style={{
                      width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                      background: 'rgba(124,58,237,0.3)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.75rem', marginBottom: 2,
                    }}>👤</div>
                  )}
                </div>
              ))}

              {/* Typing indicator */}
              {chatLoading && (
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                    background: 'linear-gradient(135deg,#7c3aed,#4f46e5)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem',
                  }}>🤖</div>
                  <div style={{
                    padding: '10px 16px', borderRadius: '16px 16px 16px 4px',
                    background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)',
                    display: 'flex', gap: 5, alignItems: 'center',
                  }}>
                    {[0, 1, 2].map(n => (
                      <div key={n} style={{
                        width: 7, height: 7, borderRadius: '50%',
                        background: '#7c3aed',
                        animation: `bounce 1.2s ${n * 0.2}s infinite`,
                      }} />
                    ))}
                  </div>
                </div>
              )}
              <div ref={chatEnd} />
            </div>

            {/* Quick suggestion chips */}
            {chatMsgs.length <= 2 && !chatLoading && (
              <div style={{ padding: '0 14px 10px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {[
                  `Explain ${topic.name} simply`,
                  'Give me an example',
                  'What are common mistakes?',
                  'How is this used in real projects?',
                ].map(chip => (
                  <button key={chip} onClick={() => {
                    setDoubt(chip);
                    setTimeout(() => inputRef.current?.focus(), 50);
                  }} style={{
                    padding: '5px 12px', borderRadius: 20, fontSize: '0.75rem',
                    background: 'rgba(124,58,237,0.15)',
                    border: '1px solid rgba(124,58,237,0.35)',
                    color: '#c4b5fd', cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}>
                    {chip}
                  </button>
                ))}
              </div>
            )}

            {/* Input bar */}
            <div style={{
              padding: '12px 14px',
              borderTop: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(0,0,0,0.2)',
              flexShrink: 0,
            }}>
              <div style={{
                display: 'flex', gap: 8, alignItems: 'flex-end',
                background: 'rgba(255,255,255,0.06)',
                borderRadius: 14,
                border: '1px solid rgba(124,58,237,0.3)',
                padding: '8px 12px',
                transition: 'border-color 0.2s',
              }}>
                <textarea
                  ref={inputRef}
                  rows={1}
                  style={{
                    flex: 1, background: 'transparent', border: 'none', outline: 'none',
                    color: '#e2e8f0', fontSize: '0.9rem', lineHeight: 1.5, resize: 'none',
                    fontFamily: 'inherit', maxHeight: 90, overflow: 'auto',
                    scrollbarWidth: 'thin',
                  }}
                  placeholder="Ask your doubt here…"
                  value={doubt}
                  onChange={e => {
                    setDoubt(e.target.value);
                    e.target.style.height = 'auto';
                    e.target.style.height = Math.min(e.target.scrollHeight, 90) + 'px';
                  }}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendDoubt(); }
                  }}
                  disabled={chatLoading}
                />
                <button
                  onClick={sendDoubt}
                  disabled={chatLoading || !doubt.trim()}
                  style={{
                    width: 36, height: 36, borderRadius: 10, border: 'none', cursor: 'pointer',
                    background: doubt.trim() && !chatLoading
                      ? 'linear-gradient(135deg,#7c3aed,#6d28d9)'
                      : 'rgba(255,255,255,0.08)',
                    color: '#fff', fontSize: '1rem', flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.2s',
                    boxShadow: doubt.trim() ? '0 2px 8px rgba(124,58,237,0.4)' : 'none',
                  }}
                >
                  ➤
                </button>
              </div>
              <p style={{ color: '#6b7280', fontSize: '0.7rem', marginTop: 6, textAlign: 'center' }}>
                Press Enter to send · Shift+Enter for new line
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bounce animation for typing dots */}
      <style>{`
        @keyframes bounce {
          0%,60%,100% { transform: translateY(0); }
          30% { transform: translateY(-6px); }
        }
        @keyframes pulse {
          0%,100% { opacity:1; }
          50% { opacity:0.5; }
        }
        @media (max-width: 680px) {
          .learn-panel  { display: ${activeTab === 'learn'  ? 'flex' : 'none'} !important; flex: 1 !important; width: auto !important; }
          .doubt-panel  { display: ${activeTab === 'doubt'  ? 'flex' : 'none'} !important; flex: 1 !important; width: auto !important; }
        }
      `}</style>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN LEARN PAGE
═══════════════════════════════════════════════════════════════ */
export default function Learn({ user }) {
  const [selectedLang, setSelectedLang]   = useState('python');
  const [ifaceLang, setIfaceLang]         = useState(user.preferred_language || 'english');
  const [topics, setTopics]               = useState([]);
  const [topicStatuses, setTopicStatuses] = useState({});
  const [topicsLoading, setTopicsLoading] = useState(false);
  const [activeTopic, setActiveTopic]     = useState(null);
  const [testTopic, setTestTopic]         = useState(null);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [notification, setNotification]   = useState({ msg: '', type: 'success' });
  const [showEditor, setShowEditor] = useState(false);


  useEffect(() => { loadAll(); }, [selectedLang]); // eslint-disable-line

  const loadAll = async () => {
    setTopicsLoading(true);
    try {
      const [tRes, sRes] = await Promise.all([
        API.get(`/courses/topics/?language=${selectedLang}`),
        API.get(`/tests/topic/status/?language=${selectedLang}`),
      ]);
      setTopics(tRes.data.topics);
      const map = {};
      sRes.data.statuses.forEach(s => { map[s.topic_id] = s; });
      setTopicStatuses(map);
    } catch (e) { console.error(e); }
    setTopicsLoading(false);
  };

  const isUnlocked = topic => {
    if (topic.order === 0) return true;
    const prev = topics.find(t => t.order === topic.order - 1);
    if (!prev) return true;
    return topicStatuses[prev.id]?.passed === true;
  };

  const notify = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification({ msg: '', type: 'success' }), 4000);
  };

  const handleTopicClick = topic => {
    if (!isUnlocked(topic)) { notify('🔒 Complete the previous topic test first!', 'error'); return; }
    setActiveTopic(topic);
  };

  const handleTestClick = () => { setTestTopic(activeTopic); setActiveTopic(null); };

  const handleTestPassed = passed => {
    setTestTopic(null);
    notify(`🎉 "${passed.name}" passed! Next topic unlocked.`, 'success');
    loadAll();
  };

  const handleTestWeak = (weak, score) => {
    setTestTopic(null);
    // Reopen lesson with doubt tab active so AI tutor can help immediately
    setActiveTopic({ ...weak, _openDoubtTab: true });
    notify(
      `🔴 Weak topic: "${weak.name}" (${score}/10). You must score 7+ to continue. Revise with the AI tutor!`,
      'error'
    );
  };

  const statusBadge = topic => {
    const s = topicStatuses[topic.id];
    if (!s || s.best_score === null || s.best_score === undefined) return null;
    return s.passed
      ? <span style={{ fontSize: '0.72rem', color: '#6ee7b7', marginLeft: 8 }}>✓ {s.best_score}/10</span>
      : <span style={{ fontSize: '0.72rem', color: '#fbbf24', marginLeft: 8 }}>⚠ {s.best_score}/10</span>;
  };

  return (
    <div>
      {/* Notification */}
      {notification.msg && (
        <div
          className={`alert ${notification.type === 'error' ? 'alert-error' : 'alert-success'}`}
          style={{ cursor: 'pointer', marginBottom: 12 }}
          onClick={() => setNotification({ msg: '', type: 'success' })}
        >
          {notification.msg} <span style={{ opacity: 0.6, fontSize: '0.8rem' }}>(click to dismiss)</span>
        </div>
      )}

      {/* Header card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <h2 className="card-title" style={{ margin: 0 }}>📖 Learn</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label className="form-label" style={{ margin: 0, whiteSpace: 'nowrap' }}>Interface:</label>
            <select className="form-select" style={{ width: 'auto' }}
              value={ifaceLang} onChange={e => setIfaceLang(e.target.value)}>
              {IFACE_LANGS.map(l => <option key={l.key} value={l.key}>{l.label}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Language selector */}
      <div className="lang-grid">
        {LANGUAGES.map(l => (
          <div key={l.key}
            className={`lang-card ${selectedLang === l.key ? 'selected' : ''}`}
            onClick={() => { setSelectedLang(l.key); setActiveTopic(null); setTestTopic(null); }}>
            <div className="lang-icon">{l.icon}</div>
            <div className="lang-name">{l.name}</div>
          </div>
        ))}
      </div>

      {/* Topic list */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <h3 className="card-title" style={{ margin: 0 }}>
            Topics — {LANGUAGES.find(l => l.key === selectedLang)?.name}
          </h3>
          <button className="btn btn-outline" style={{ fontSize: '0.85rem', padding: '7px 16px' }}
            onClick={() => setShowLeaderboard(true)}>
            🏆 Leaderboard
          </button>
          <button
                 className="btn btn-outline"
                 style={{ fontSize: '.85rem', padding: '7px 16px', color: '#10b981', borderColor: '#059669' }}
                onClick={() => setShowEditor(true)}>
                   💻 Practice</button>
        </div>

        {topicsLoading ? <div className="spinner" /> : topics.length === 0 ? (
          <p className="text-muted">No topics found. Try refreshing.</p>
        ) : (
          <div className="topic-list">
            {topics.map(topic => {
              const unlocked  = isUnlocked(topic);
              const status    = topicStatuses[topic.id];
              const passed    = status?.passed === true;
              const attempted = status?.best_score !== null && status?.best_score !== undefined;

              return (
                <div key={topic.id}
                  className={`topic-item ${passed ? 'done' : ''}`}
                  style={{ opacity: unlocked ? 1 : 0.42, cursor: unlocked ? 'pointer' : 'not-allowed' }}
                  onClick={() => handleTopicClick(topic)}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span className="topic-name">
                        {!unlocked ? '🔒 ' : passed ? '✅ ' : ''}{topic.order + 1}. {topic.name}
                      </span>
                      {statusBadge(topic)}
                    </div>
                    <p style={{ fontSize: '0.74rem', color: '#9ca3af', marginTop: 2 }}>
                      {!unlocked ? 'Pass previous topic test to unlock'
                        : passed ? `Test passed (${status.best_score}/10) — click to review or retake`
                        : attempted ? `Test attempted (${status.best_score}/10) — click to retry`
                        : 'Click to open lesson → read → take topic test'}
                    </p>
                  </div>
                  <span className={`topic-badge ${passed ? 'badge-done' : 'badge-pending'}`}
                    style={{ flexShrink: 0, marginLeft: 8 }}>
                    {passed ? '✓ Passed' : unlocked ? 'Open →' : '🔒'}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* How-to guide */}
        {topics.length > 0 && (
          <div style={{
            marginTop: 16, padding: '12px 16px',
            background: 'rgba(124,58,237,0.08)',
            borderRadius: 12, border: '1px solid rgba(124,58,237,0.2)',
          }}>
            <p style={{ fontSize: '0.8rem', color: '#c4b5fd', fontWeight: 600, marginBottom: 4 }}>📋 How to progress:</p>
            <p style={{ fontSize: '0.76rem', color: '#9ca3af', lineHeight: 1.8 }}>
              1. Click a topic → 2. Read lesson (left panel) → 3. Ask doubts (right panel) →
              4. Scroll to bottom → 5. Take Topic Test (score <strong style={{ color: '#e2e8f0' }}>7+/10</strong> to unlock next) →
              6. After all topics passed → Course Test → Certificate 🏆
            </p>
          </div>
        )}
      </div>

      {/* Lesson two-panel modal */}
      {activeTopic && !testTopic && (
        <LessonModal
          topic={activeTopic}
          ifaceLang={ifaceLang}
          topicStatus={topicStatuses[activeTopic.id]}
          onClose={() => setActiveTopic(null)}
          onTestClick={handleTestClick}
        />
      )}

      {/* Topic test modal */}
      {testTopic && (
        <TopicTestModal
          topic={testTopic}
          ifaceLang={ifaceLang}
          onClose={() => setTestTopic(null)}
          onPassed={handleTestPassed}
          onWeak={handleTestWeak}
        />
      )}

      {/* Leaderboard */}
      {showLeaderboard && (
        <LeaderboardModal lang={selectedLang} onClose={() => setShowLeaderboard(false)} />
      )}
         {showEditor && (<CodeEditor
             language={selectedLang === 'java' ? 'java' : 'python'}
             onClose={() => setShowEditor(false)}
  />
)}

    </div>
  );
}