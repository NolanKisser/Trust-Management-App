import React from 'react';
import './App.css';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { StatCard } from './components/StatCard';
import { GatewayCard } from './components/GatewayCard';
import { DeviceTable } from './components/DeviceTable';
import { mockData } from './data/mockData';

function App() {
  const { networkOverview, gateways, alerts, devices } = mockData;

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
          
          {/* Network Overview */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Network Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard icon="🛡️" title="Avg Trust Score" value={networkOverview.avgTrustScore} type="success" />
              <StatCard icon="⚠️" title="Devices at Risk" value={networkOverview.devicesAtRisk} type="warning" />
              <StatCard icon="🌐" title="Active Gateways" value={networkOverview.activeGateways} type="info" />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Main Content (Gateways & Devices) */}
            <div className="lg:col-span-2 space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {gateways.map(gateway => (
                  <GatewayCard key={gateway.id} gateway={gateway} />
                ))}
              </div>
              <DeviceTable devices={devices} />
            </div>

            {/* Sidebar Content (Alerts & LLM Assistant) */}
            <div className="space-y-6">
              <div className="bg-white p-4 rounded-lg shadow-sm">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">Alerts</h2>
                {alerts.map(alert => (
                  <div key={alert.id} className="mb-3 pb-3 border-b border-gray-100 last:border-0">
                    <p className="font-semibold text-red-600 text-sm">⚠️ {alert.title} <span className="text-gray-400 font-normal">{alert.time}</span></p>
                    <p className="text-sm text-gray-600 ml-6">• {alert.device}</p>
                  </div>
                ))}
              </div>

              <div className="bg-white p-4 rounded-lg shadow-sm">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">LLM Assistant</h2>
                <div className="bg-gray-50 p-3 rounded-md text-sm text-gray-700 mb-4 border border-gray-200">
                  <p className="font-medium text-gray-900 mb-2">Why did this device lose trust?</p>
                  <p>Trust dropped due to repeated ON-OFF behavior combined with abnormal proximity changes.</p>
                </div>
                <div className="space-x-2">
                  <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md text-sm">Apply Fix</button>
                  <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded-md text-sm">Log Only</button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;