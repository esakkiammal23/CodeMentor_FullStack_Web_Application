import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import Learn from './components/Learn';
import Test from './components/Test';
import Certificates from './components/Certificates';
import LandingPage from './components/LandingPage';

import './index.css';

export default function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");

    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem("user");
      }
    }
  }, []);

  const handleLogin = (userData, token) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <Router>

       {user && <Navbar user={user} onLogout={handleLogout} />} 

      <Routes>

        {/* Public */}

        <Route
          path="/"
          element={
            user
              ? <Navigate to="/dashboard" replace />
              : <LandingPage onLogin={handleLogin} />
          }
        />

        <Route
          path="/login"
          element={
            user
              ? <Navigate to="/dashboard" replace />
              : <LandingPage onLogin={handleLogin} startModal="login" />
          }
        />

        <Route
          path="/register"
          element={
            user
              ? <Navigate to="/dashboard" replace />
              : <LandingPage onLogin={handleLogin} startModal="register" />
          }
        />

        {/* Protected */}

        <Route
          path="/dashboard"
          element={
            user
              ? <div className="app-container"><Dashboard user={user} /></div>
              : <Navigate to="/" replace />
          }
        />

        <Route
          path="/learn"
          element={
            user
              ? <div className="app-container"><Learn user={user} /></div>
              : <Navigate to="/" replace />
          }
        />

        <Route
          path="/test"
          element={
            user
              ? <div className="app-container"><Test user={user} /></div>
              : <Navigate to="/" replace />
          }
        />

        <Route
          path="/certificates"
          element={
            user
              ? <div className="app-container"><Certificates /></div>
              : <Navigate to="/" replace />
          }
        />

      </Routes>
    </Router>
  );
}