import React from 'react';

export function StatCard({ icon, title, value, type, darkMode }) {
  const colourClasses = {
    success: 'text-green-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500',
  };
  return (
    <div className={`p-5 rounded-xl shadow-sm flex items-center border ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-200'} transition-transform hover:-translate-y-0.5`}>
      <div className={`text-3xl mr-4 ${colourClasses[type]}`}>{icon}</div>
      <div>
        <h3 className={`text-xs uppercase tracking-wide ${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>{title}</h3>
        <p className={`text-3xl font-bold tracking-tight ${darkMode ? 'text-slate-100' : 'text-gray-900'}`}>{value}</p>
      </div>
    </div>
  );
}