import React from 'react';

export function Sidebar() {
  return (
    <div className="bg-gray-800 text-white w-64 flex flex-col">
      <div className="h-16 flex items-center pl-6 text-xl font-semibold border-b border-gray-700">
        <span className="text-blue-400 mr-2">🛡️</span> TMS
      </div>
      <nav className="flex-1 px-4 py-6 space-y-2">
        <a href="#" className="flex items-center px-4 py-2 text-gray-300 hover:bg-gray-700 rounded-md">
          Dashboard
        </a>
        <a href="#" className="flex items-center px-4 py-2 bg-gray-700 text-white rounded-md">
          Gateways
        </a>
        <a href="#" className="flex items-center px-4 py-2 text-gray-300 hover:bg-gray-700 rounded-md">
          Devices
        </a>
        <a href="#" className="flex items-center px-4 py-2 text-gray-300 hover:bg-gray-700 rounded-md justify-between">
          Alerts
          <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">2</span>
        </a>
        <a href="#" className="flex items-center px-4 py-2 text-gray-300 hover:bg-gray-700 rounded-md">
          Settings
        </a>
      </nav>
    </div>
  );
}