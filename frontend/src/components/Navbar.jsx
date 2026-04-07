import React from 'react';

export function Navbar({ darkMode }) {
  const now = new Date();
  const formattedDate = now.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  const formattedTime = now.toLocaleTimeString();

  return (
    <header className={`h-16 flex items-center justify-between px-6 border-b ${darkMode ? 'bg-slate-900/90 border-slate-700' : 'bg-white/90 border-gray-200'} backdrop-blur`}>
      <div>
        <h1 className={`text-xl font-semibold tracking-tight ${darkMode ? 'text-slate-100' : 'text-gray-900'}`}>Trust Management System</h1>
        <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>Real-time Device Trust Analytics</p>
      </div>
      <div className={`text-right text-xs ${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>
        <div>{formattedDate}</div>
        <div className="font-mono">{formattedTime}</div>
      </div>
    </header>
  );
}