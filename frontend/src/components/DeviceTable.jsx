import React from 'react';

export function DeviceTable({ devices }) {
  const getStatusClass = (status) => {
    switch (status) {
      case 'Normal': return 'bg-green-100 text-green-800';
      case 'At Risk': return 'bg-red-100 text-red-800';
      case 'Warning': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="font-semibold text-gray-800">Connected Devices</h2>
      </div>
      <table className="w-full text-left">
        <thead className="bg-gray-50 text-gray-600 text-sm uppercase font-semibold">
          <tr>
            <th className="px-6 py-3">Device ID</th>
            <th className="px-6 py-3">Trust Score</th>
            <th className="px-6 py-3">Status</th>
            <th className="px-6 py-3">Profile</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 text-sm text-gray-700">
          {devices.map((device) => (
            <tr key={device.id}>
              <td className="px-6 py-4 font-medium">{device.id}</td>
              <td className="px-6 py-4">
                <span className={`font-bold mr-2 ${device.trustScore > 0.8 ? 'text-green-600' : device.trustScore < 0.5 ? 'text-red-600' : 'text-yellow-600'}`}>
                  {device.trustScore}
                </span>
              </td>
              <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusClass(device.status)}`}>
                  {device.status}
                </span>
              </td>
              <td className="px-6 py-4">{device.profile}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}