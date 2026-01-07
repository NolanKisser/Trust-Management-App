import React from 'react';

export function Navbar() {
  return (
    <header className="bg-white h-16 flex items-center justify-between px-6 border-b border-gray-200">
      <h1 className="text-xl font-semibold text-gray-800">Trust Management System</h1>
      <div className="flex items-center">
        <span className="text-gray-600 mr-2">analyst_user</span>
        <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
      </div>
    </header>
  );
}