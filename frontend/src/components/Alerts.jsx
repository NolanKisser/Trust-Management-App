import React from 'react';

export function Alerts({ devices }) {
  const problematicDevices = devices.filter(d => d.status === 'At Risk' || d.status === 'Warning');

  let alertContent;

  if (problematicDevices.length === 0) {
    alertContent = (
      <div className="p-8 text-center text-gray-500">
        <span className="block text-4xl mb-2">🛡️</span>
        <p>No active security threats or warnings.</p>
      </div>
    );
  } else {
    alertContent = (
      <div>
        {problematicDevices.map(device => {
          const classMatch = (device.profile || "").match(/Class (\d+)/);
          const deviceBehaviourClass = classMatch ? parseInt(classMatch[1], 10) : 0;
          const isRisk = device.status === 'At Risk';

          let alertDetails = isRisk ? {
            themeColour: "bg-red-50 hover:bg-red-100 border-red-200",
            textColour: "text-red-800",
            icon: "⚠️",
            severity: "Critical",
            title: "Active Attack Pattern",
            desc: `Analysis: AI classification ${deviceBehaviourClass} (Attack Range) indicates malicious behavior. Please note that trust does not matter in this case.`
          } : {
            themeColour: "bg-yellow-50 hover:bg-yellow-100 border-yellow-200",
            textColour: "text-yellow-800",
            icon: "📉",
            severity: "Moderate",
            title: "Trust Degradation",
            desc: `Analysis: Device behavior is Normal (Class ${deviceBehaviourClass}), but Trust Score has dropped below safe threshold.`
          };

          return (
            <div key={device.id} className={`p-4 flex items-start border-b border-gray-200 last:border-b-0 transition-colors ${alertDetails.themeColour}`}>
              <div className="shrink-0 mr-4 mt-1 text-2xl">
                <span>{alertDetails.icon}</span>
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className={`text-lg font-bold leading-tight ${alertDetails.textColour}`}>
                      {alertDetails.title}
                    </h4>
                    <span className={`block text-xs uppercase font-bold tracking-wide opacity-80 ${alertDetails.textColour}`}>
                      {alertDetails.severity} Severity • {device.id}
                    </span>
                  </div>
                  <span className={`font-mono text-xs px-2 py-1 rounded border bg-white ${isRisk ? 'border-red-200 text-red-800' : 'border-yellow-200 text-yellow-800'}`}>
                    {device.profile}
                  </span>
                </div>
                <p className={`text-sm mt-2 ${alertDetails.textColour}`}>
                   {alertDetails.desc}
                </p>
                <div className={`mt-2 text-sm p-2 rounded border inline-block ${isRisk ? 'bg-red-100/50 border-red-100' : 'bg-yellow-100/50 border-yellow-100'}`}>
                  <span className={`font-semibold ${isRisk ? 'text-red-900' : 'text-yellow-900'}`}>Trust Score: </span> 
                  <span className={`font-mono ${alertDetails.textColour}`}>{device.trustDisplay}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-semibold text-gray-800">System Alerts</h2>
      
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="font-semibold text-gray-800">Active Issues</h3>
          <span className="bg-gray-100 text-gray-700 text-xs font-semibold px-2.5 py-0.5 rounded-full">
            {problematicDevices.length} Detected
          </span>
        </div>
        
        {alertContent}

      </div>
    </div>
  );
}