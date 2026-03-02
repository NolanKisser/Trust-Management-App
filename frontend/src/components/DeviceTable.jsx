import React from 'react';

export function DeviceTable({ devices, onDeviceClick }) {
  const getStatusClass = (status) => {
    switch (status) {
      case 'Normal': return 'bg-green-100 text-green-800';
      case 'At Risk': return 'bg-red-100 text-red-800';
      case 'Warning': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="font-semibold text-gray-800 text-lg">Connected Devices</h2>
        <span className="text-xs text-gray-400 font-mono">Real-time update active</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-bold tracking-wider">
            <tr>
              <th className="px-6 py-4">Device ID</th>
              <th className="px-6 py-4">Trust Score</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Profile / Classification</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 text-sm text-gray-700">
            {devices.map((device) => (
              <tr key={device.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 font-semibold text-blue-600 cursor-pointer" onClick={() => onDeviceClick(device)}>
                  {device.id}
                </td>
                <td className="px-6 py-4">
                  <span className="font-mono text-gray-600 font-medium bg-gray-100 px-2 py-1 rounded">
                    {device.trustDisplay || "Calculating..."}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${getStatusClass(device.status)}`}>
                    {device.status}
                  </span>
                </td>
                <td className="px-6 py-4 font-medium text-gray-600 italic">
                    {device.profile || "Waiting..."}
                </td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => onDeviceClick(device)}
                    className="text-xs bg-blue-50 text-blue-600 px-3 py-1.5 rounded-md hover:bg-blue-600 hover:text-white transition-all font-semibold border border-blue-100"
                  >
                    🧠 Analyze
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}