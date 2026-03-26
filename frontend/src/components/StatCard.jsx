import React from 'react';

export function StatCard({ icon, title, value, type, darkMode }) {
  const colourClasses = {
    success: 'text-green-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500',
  };
  return (
    <div className={`p-4 rounded-lg shadow-sm flex items-center border ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-100'}`}>
      <div className={`text-3xl mr-4 ${colourClasses[type]}`}>{icon}</div>
      <div>
        <h3 className={`text-sm ${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>{title}</h3>
        <p className={`text-2xl font-bold ${darkMode ? 'text-slate-100' : 'text-gray-800'}`}>{value}</p>
      </div>
    </div>
  );
}