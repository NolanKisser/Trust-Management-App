import React from 'react';

export function StatCard({ icon, title, value, type }) {
  const colorClasses = {
    success: 'text-green-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500',
  };
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm flex items-center">
      <div className={`text-3xl mr-4 ${colorClasses[type]}`}>{icon}</div>
      <div>
        <h3 className="text-gray-500 text-sm">{title}</h3>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  );
}