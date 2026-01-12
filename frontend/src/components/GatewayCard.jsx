import React from 'react';

export function GatewayCard({ gateway }) {
  const isSuspect = gateway.status === 'Suspect';
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-gray-700">{gateway.name}</h3>
          <p className="text-sm text-gray-500">{gateway.devices} Devices 
            {gateway.atRisk > 0 && (
              <span className="text-red-600 font-medium ml-2">
                ({gateway.atRisk} At Risk)
              </span>
            )}
          </p>
        </div>
        <span className="text-gray-400">...</span>
      </div>
      <div className={`flex items-center p-2 rounded-md ${isSuspect ? 'bg-yellow-100' : 'bg-green-100'}`}>
        <span className={`mr-2 ${isSuspect ? 'text-yellow-600' : 'text-green-600'}`}>
          {isSuspect ? '⚠️' : '✔️'}
        </span>
        <span className={`font-semibold ${isSuspect ? 'text-yellow-800' : 'text-green-800'}`}>
          {gateway.status} {gateway.score}
        </span>
      </div>
    </div>
  );
}