import React, { useState, useEffect } from 'react';
import './App.css';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { StatCard } from './components/StatCard';
import { GatewayCard } from './components/GatewayCard';
import { DeviceTable } from './components/DeviceTable';

function App() {
  const [data, setData] = useState(null);

  const fetchData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dashboard');
      if (response.ok) {
        const jsonData = await response.json();
        setData(jsonData);
      }
    } catch (error) {
      console.error("Connection error:", error);
    }
  };

  useEffect(() => {
    fetchData(); // Initial Fetch
    const interval = setInterval(fetchData, 2000); // Auto-Refresh every 2s
    return () => clearInterval(interval);
  }, []);

  if (!data) return <div className="p-10">Waiting for Backend...</div>;

  const { networkOverview, devices } = data;

  // Generate Dummy Gateways for UI visualization
  const gateways = [
    { id: 'A', name: 'Gateway A', devices: devices.length, status: 'OK', score: 0.92 }
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Network Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard icon="🛡️" title="Avg Trust Score" value={networkOverview.avgTrustScore} type="success" />
              <StatCard icon="⚠️" title="Devices at Risk" value={networkOverview.devicesAtRisk} type="warning" />
              <StatCard icon="🌐" title="Active Gateways" value={networkOverview.activeGateways} type="info" />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="grid grid-cols-1">
                 {gateways.map(g => <GatewayCard key={g.id} gateway={g} />)}
              </div>
              <DeviceTable devices={devices} />
            </div>
            
            {/* Simple Sidebar placeholder */}
            <div className="space-y-6">
               <div className="bg-white p-4 rounded shadow">
                 <h3 className="font-bold text-gray-700">System Logs</h3>
                 <p className="text-sm text-gray-500 mt-2">Listening for network traffic...</p>
               </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
export default App;