import React, { useState, useRef, useEffect, useCallback } from 'react';
import API from '../api';

/* ═══════════════════════════════════════════════════════════════
   LANGUAGE CONFIG — add JavaScript, SQL etc here in future
═══════════════════════════════════════════════════════════════ */
const LANGUAGES = {
  python: {
    key: 'python', label: 'Python', icon: '🐍', color: '#3b82f6',
    ext: 'py',
    starter: `# ── Python Practice ──────────────────────────────────
# Write your code and click ▶ Run  (Ctrl+Enter)

def greet(name):
    return f"Hello, {name}! Welcome to CodeMentor 🎓"

print(greet("Student"))

# Lists & loops
numbers = [1, 2, 3, 4, 5]
squares = [n ** 2 for n in numbers]
print("Squares:", squares)

for i, sq in enumerate(squares, 1):
    print(f"  {i}² = {sq}")
`,
  },
  java: {
    key: 'java', label: 'Java', icon: '☕', color: '#f59e0b',
    ext: 'java',
    starter: `// ── Java Practice ────────────────────────────────────
// Write your code and click ▶ Run  (Ctrl+Enter)

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, CodeMentor! 🎓");

        // Loop example
        for (int i = 1; i <= 5; i++) {
            System.out.println("Count: " + i);
        }

        // Method call
        System.out.println(greet("Student"));
    }

    static String greet(String name) {
        return "Welcome, " + name + "!";
    }
}
`,
  },
  // ── Future ─────────────────────────────────────────────────
  // javascript: { key:'javascript', label:'JavaScript', icon:'🟨', color:'#eab308', ext:'js', starter:'// JS\nconsole.log("Hello!");' },
  // sql:        { key:'sql',        label:'SQL',        icon:'🗄️',  color:'#06b6d4', ext:'sql', starter:'SELECT 1+1 AS result;' },
};

/* ═══════════════════════════════════════════════════════════════
   LINE NUMBERS
═══════════════════════════════════════════════════════════════ */
function LineNumbers({ count, fontSize, lineHeight }) {
  return (
    <div style={{
      padding: `${lineHeight * 0.875}px 0`,
      minWidth: 48, flexShrink: 0,
      background: 'rgba(0,0,0,0.18)',
      borderRight: '1px solid rgba(255,255,255,0.05)',
      textAlign: 'right',
      userSelect: 'none',
      overflowY: 'hidden',
    }}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} style={{
          padding: '0 10px',
          fontSize,
          lineHeight: `${lineHeight}px`,
          height: lineHeight,
          color: '#394562',
          fontFamily: "'JetBrains Mono','Fira Code',monospace",
        }}>
          {i + 1}
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   CODE EDITOR MODAL
═══════════════════════════════════════════════════════════════ */
export default function CodeEditor({ language: initLang = 'python', onClose }) {
  const safeInit = initLang in LANGUAGES ? initLang : 'python';
  const [lang, setLang]           = useState(safeInit);
  const [code, setCode]           = useState(LANGUAGES[safeInit].starter);
  const [output, setOutput]       = useState('');
  const [running, setRunning]     = useState(false);
  const [activeTab, setActiveTab] = useState('code');
  const [fontSize, setFontSize]   = useState(14);
  const [runCount, setRunCount]   = useState(0);
  const [runTime, setRunTime]     = useState(null);
  const [status, setStatus]       = useState(null); // 'ok' | 'error' | null
  const textareaRef = useRef(null);
  const outputRef   = useRef(null);
  const cfg = LANGUAGES[lang];
  const LINE_H = Math.round(fontSize * 1.65);

  /* ── Lock body scroll ── */
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  /* ── Sync textarea scroll with line numbers ── */
  const syncScroll = () => {
    // handled by shared overflow container
  };

  /* ── Switch language ── */
  const switchLang = (l) => {
    setLang(l);
    setCode(LANGUAGES[l].starter);
    setOutput('');
    setStatus(null);
    setRunTime(null);
  };

  /* ── Tab key + Ctrl+Enter ── */
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const s = e.target.selectionStart;
      const end = e.target.selectionEnd;
      const next = code.slice(0, s) + '    ' + code.slice(end);
      setCode(next);
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = s + 4;
          textareaRef.current.selectionEnd   = s + 4;
        }
      });
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleRun();
    }
  }, [code]);

  /* ── Auto scroll output ── */
  useEffect(() => {
    if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [output]);

  /* ── RUN ── */
  const handleRun = async () => {
    if (running) return;
    setRunning(true);
    setOutput('');
    setStatus(null);
    setActiveTab('output');
    const t0 = Date.now();

    try {
      const res = await API.post('/tests/run-code/', { code, language: lang });
      const elapsed = ((Date.now() - t0) / 1000).toFixed(2);
      setRunTime(elapsed);
      setRunCount(c => c + 1);

      const stdout      = (res.data.stdout      || '').trimEnd();
      const stderr      = (res.data.stderr      || '').trimEnd();
      const compile_err = (res.data.compile_err || '').trimEnd();

      if (compile_err) {
        setOutput(compile_err);
        setStatus('error');
      } else if (stderr && !stdout) {
        setOutput(stderr);
        setStatus('error');
      } else if (stdout) {
        setOutput(stdout + (stderr ? '\n\n[stderr]\n' + stderr : ''));
        setStatus('ok');
      } else {
        setOutput('(Program finished with no output)');
        setStatus('ok');
      }
    } catch (err) {
      const msg = err.response?.data?.compile_err
               || err.response?.data?.error
               || err.message || 'Unknown error';
      setOutput('⚠️ ' + msg);
      setStatus('error');
      setRunTime(null);
    }
    setRunning(false);
  };

  const lineCount = code.split('\n').length;

  const S = {
    topBar: {
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '9px 14px',
      background: '#161b22',
      borderBottom: '1px solid #21262d',
      flexShrink: 0, flexWrap: 'wrap',
    },
    panelHeader: {
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '6px 13px',
      background: '#161b22',
      borderBottom: '1px solid #21262d',
      flexShrink: 0,
    },
    smallBtn: (active) => ({
      padding: '4px 12px', borderRadius: 7,
      border: `1px solid ${active ? cfg.color : '#30363d'}`,
      background: active ? `${cfg.color}1a` : 'transparent',
      color: active ? cfg.color : '#8b949e',
      fontSize: '.76rem', fontWeight: 700,
      cursor: 'pointer', transition: 'all .15s',
      fontFamily: "'Sora',sans-serif",
    }),
    runBtn: {
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '9px 26px', borderRadius: 9,
      background: running ? 'rgba(0,212,255,.1)' : '#00d4ff',
      border: running ? '1px solid rgba(0,212,255,.3)' : 'none',
      color: running ? '#00d4ff' : '#0a0e1a',
      fontSize: '.92rem', fontWeight: 800,
      cursor: running ? 'not-allowed' : 'pointer',
      fontFamily: "'Sora',sans-serif",
      boxShadow: running ? 'none' : '0 0 20px rgba(0,212,255,.3)',
      transition: 'all .2s',
    },
  };

  return (
    <div
      onClick={e => e.target === e.currentTarget && onClose()}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.88)',
        backdropFilter: 'blur(10px)',
        zIndex: 2000,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 12,
      }}
    >
      <div style={{
        width: '100%', maxWidth: 1200,
        height: '92vh',
        background: '#0d1117',
        borderRadius: 18,
        border: '1px solid #21262d',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 32px 100px rgba(0,0,0,0.85)',
        fontFamily: "'Sora','Segoe UI',sans-serif",
      }}>

        {/* ══ TOP BAR ══════════════════════════════════════════ */}
        <div style={S.topBar}>
          {/* macOS dots */}
          <div style={{ display: 'flex', gap: 6 }}>
            {['#ff5f57','#ffbd2e','#28c840'].map((c, i) => (
              <div key={i} onClick={i === 0 ? onClose : undefined}
                style={{ width: 13, height: 13, borderRadius: '50%', background: c, cursor: i === 0 ? 'pointer' : 'default' }} />
            ))}
          </div>

          {/* Title */}
          <div style={{ flex: 1, textAlign: 'center', fontSize: '.78rem', color: '#8b949e', fontFamily: "'JetBrains Mono',monospace" }}>
            <span style={{ color: cfg.color }}>{cfg.icon} {cfg.label}</span>
            <span style={{ color: '#3d444d' }}> — CodeMentor Practice Editor</span>
          </div>

          {/* Language switcher */}
          <div style={{ display: 'flex', gap: 5 }}>
            {Object.values(LANGUAGES).map(l => (
              <button key={l.key} onClick={() => switchLang(l.key)} style={S.smallBtn(lang === l.key)}>
                {l.icon} {l.label}
              </button>
            ))}
          </div>

          {/* Font size */}
          <div style={{ display: 'flex', gap: 4 }}>
            {[12, 14, 16].map(s => (
              <button key={s} onClick={() => setFontSize(s)}
                style={{
                  width: 27, height: 27, borderRadius: 6,
                  border: `1px solid ${fontSize === s ? '#00d4ff' : '#30363d'}`,
                  background: fontSize === s ? 'rgba(0,212,255,.12)' : 'transparent',
                  color: fontSize === s ? '#00d4ff' : '#8b949e',
                  fontSize: '.65rem', fontWeight: 800, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                {s === 12 ? 'S' : s === 14 ? 'M' : 'L'}
              </button>
            ))}
          </div>

          {/* Close */}
          <button onClick={onClose} style={{
            background: 'transparent', border: '1px solid #30363d',
            color: '#8b949e', width: 28, height: 28, borderRadius: 8,
            cursor: 'pointer', fontSize: '.9rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>✕</button>
        </div>

        {/* ══ BODY ══════════════════════════════════════════════ */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

          {/* ── LEFT: CODE ──────────────────────────────────── */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid #21262d' }}>

            {/* Editor header */}
            <div style={S.panelHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: cfg.color, boxShadow: `0 0 8px ${cfg.color}99` }} />
                <span style={{ fontSize: '.74rem', color: '#8b949e', fontFamily: "'JetBrains Mono',monospace" }}>
                  {lang === 'java' ? 'Main.java' : 'main.py'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: '.66rem', color: '#3d444d', fontFamily: 'monospace' }}>Ctrl+Enter to run</span>
                <button onClick={() => { setCode(cfg.starter); setOutput(''); setStatus(null); }}
                  style={{ padding: '3px 10px', borderRadius: 6, background: 'transparent', border: '1px solid #30363d', color: '#8b949e', fontSize: '.7rem', cursor: 'pointer', fontFamily: "'Sora',sans-serif" }}>
                  Reset
                </button>
              </div>
            </div>

            {/* Code area */}
            <div style={{ flex: 1, display: 'flex', overflow: 'auto', background: '#0d1117' }}>
              <LineNumbers count={lineCount} fontSize={`${fontSize}px`} lineHeight={LINE_H} />
              <textarea
                ref={textareaRef}
                value={code}
                onChange={e => setCode(e.target.value)}
                onKeyDown={handleKeyDown}
                onScroll={syncScroll}
                spellCheck={false}
                autoCorrect="off"
                autoCapitalize="off"
                style={{
                  flex: 1, background: 'transparent',
                  border: 'none', outline: 'none',
                  color: '#e6edf3',
                  fontSize: `${fontSize}px`,
                  lineHeight: `${LINE_H}px`,
                  fontFamily: "'JetBrains Mono','Fira Code','Courier New',monospace",
                  padding: `${Math.round(LINE_H * 0.875)}px 16px`,
                  resize: 'none',
                  whiteSpace: 'pre',
                  overflowWrap: 'normal',
                  overflow: 'auto',
                  tabSize: 4,
                  caretColor: '#00d4ff',
                  minHeight: '100%',
                }}
              />
            </div>

            {/* Run bar */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '10px 14px',
              background: '#161b22',
              borderTop: '1px solid #21262d',
              flexShrink: 0,
            }}>
              <button onClick={handleRun} disabled={running} style={S.runBtn}>
                {running ? (
                  <>
                    <span style={{
                      width: 13, height: 13,
                      border: '2px solid rgba(0,212,255,.25)',
                      borderTop: '2px solid #00d4ff',
                      borderRadius: '50%',
                      display: 'inline-block',
                      animation: 'ce_spin .65s linear infinite',
                    }} />
                    Running…
                  </>
                ) : '▶  Run'}
              </button>

              <div style={{ display: 'flex', gap: 10 }}>
                {runCount > 0 && <span style={{ fontSize: '.68rem', color: '#3d444d', fontFamily: 'monospace' }}>Runs: {runCount}</span>}
                {runTime   && <span style={{ fontSize: '.68rem', color: '#3d444d', fontFamily: 'monospace' }}>{runTime}s</span>}
              </div>

              <div style={{ marginLeft: 'auto', fontSize: '.66rem', color: '#3d444d', fontFamily: 'monospace' }}>
                {lineCount} lines · {code.length} chars
              </div>
            </div>
          </div>

          {/* ── RIGHT: OUTPUT ───────────────────────────────── */}
          <div style={{ width: 430, minWidth: 300, display: 'flex', flexDirection: 'column' }}>

            {/* Output header */}
            <div style={S.panelHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 8, height: 8, borderRadius: '50%', transition: 'all .3s',
                  background: status === 'error' ? '#ef4444' : status === 'ok' ? '#10b981' : '#3d444d',
                  boxShadow: status === 'error' ? '0 0 8px #ef4444' : status === 'ok' ? '0 0 8px #10b981' : 'none',
                }} />
                <span style={{ fontSize: '.74rem', color: '#8b949e', fontFamily: "'JetBrains Mono',monospace" }}>
                  Output
                </span>
                {status === 'error' && (
                  <span style={{ fontSize: '.62rem', background: 'rgba(239,68,68,.14)', border: '1px solid rgba(239,68,68,.3)', color: '#f87171', padding: '1px 8px', borderRadius: 20, fontWeight: 800 }}>
                    ERROR
                  </span>
                )}
                {status === 'ok' && (
                  <span style={{ fontSize: '.62rem', background: 'rgba(16,185,129,.12)', border: '1px solid rgba(16,185,129,.3)', color: '#34d399', padding: '1px 8px', borderRadius: 20, fontWeight: 800 }}>
                    SUCCESS
                  </span>
                )}
              </div>
              {output && (
                <button onClick={() => { setOutput(''); setStatus(null); setRunTime(null); }}
                  style={{ padding: '3px 10px', borderRadius: 6, background: 'transparent', border: '1px solid #30363d', color: '#8b949e', fontSize: '.7rem', cursor: 'pointer', fontFamily: "'Sora',sans-serif" }}>
                  Clear
                </button>
              )}
            </div>

            {/* Output body */}
            <div ref={outputRef} style={{
              flex: 1, padding: 16, overflowY: 'auto', background: '#0d1117',
              scrollbarWidth: 'thin', scrollbarColor: '#30363d transparent',
            }}>

              {/* Idle */}
              {!output && !running && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 14, opacity: .3 }}>
                  <div style={{ fontSize: '3rem' }}>▶</div>
                  <p style={{ color: '#8b949e', fontSize: '.85rem', textAlign: 'center', margin: 0, lineHeight: 1.6 }}>
                    Click <strong style={{ color: '#e6edf3' }}>Run</strong> or press{' '}
                    <span style={{ background: '#21262d', border: '1px solid #30363d', borderRadius: 4, padding: '1px 6px', fontSize: '.75rem', fontFamily: 'monospace', color: '#8b949e' }}>
                      Ctrl+Enter
                    </span>
                    {' '}to execute your code
                  </p>
                </div>
              )}

              {/* Running */}
              {running && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 18 }}>
                  <div style={{
                    width: 46, height: 46,
                    border: '3px solid #21262d',
                    borderTop: `3px solid ${cfg.color}`,
                    borderRadius: '50%',
                    animation: 'ce_spin .7s linear infinite',
                  }} />
                  <p style={{ color: '#8b949e', fontSize: '.85rem', margin: 0 }}>
                    Executing {cfg.label} code…
                  </p>
                </div>
              )}

              {/* Output text */}
              {output && !running && (
                <>
                  {runTime && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, paddingBottom: 12, borderBottom: '1px solid #21262d' }}>
                      <span style={{
                        fontSize: '.7rem', fontWeight: 800,
                        background: status === 'error' ? 'rgba(239,68,68,.12)' : 'rgba(16,185,129,.12)',
                        border: `1px solid ${status === 'error' ? 'rgba(239,68,68,.3)' : 'rgba(16,185,129,.3)'}`,
                        color: status === 'error' ? '#f87171' : '#34d399',
                        padding: '2px 10px', borderRadius: 20,
                      }}>
                        {status === 'error' ? '✗ Error' : '✓ Success'}
                      </span>
                      <span style={{ fontSize: '.7rem', color: '#3d444d', fontFamily: 'monospace' }}>
                        {runTime}s · {cfg.icon} {cfg.label}
                      </span>
                    </div>
                  )}
                  <pre style={{
                    margin: 0,
                    fontFamily: "'JetBrains Mono','Fira Code',monospace",
                    fontSize: `${fontSize}px`,
                    lineHeight: '1.65',
                    color: status === 'error' ? '#f87171' : '#e6edf3',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}>
                    {output}
                  </pre>
                </>
              )}
            </div>

            {/* Footer */}
            <div style={{ padding: '7px 14px', background: '#161b22', borderTop: '1px solid #21262d', flexShrink: 0 }}>
              <p style={{ fontSize: '.64rem', color: '#3d444d', fontFamily: "'JetBrains Mono',monospace", textAlign: 'center', margin: 0 }}>
                Runs on your local server · Python 3 & Java supported
              </p>
            </div>
          </div>
        </div>
      </div>

      <style>{`@keyframes ce_spin { to { transform:rotate(360deg); } }`}</style>
    </div>
  );
}