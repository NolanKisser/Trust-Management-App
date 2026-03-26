import React from 'react';

export function Navbar({ darkMode }) {
  return (
    <header className={`h-16 flex items-center justify-between px-6 border-b ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-200'}`}>
      <h1 className={`text-xl font-semibold ${darkMode ? 'text-slate-100' : 'text-gray-800'}`}>Trust Management System</h1>
    </header>
  );
}