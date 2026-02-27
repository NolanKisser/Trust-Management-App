import React, { useState, useEffect } from 'react';
import './App.css'; // Ensure this contains @tailwind directives
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { StatCard } from './components/StatCard';
import { Alerts } from './components/Alerts';
import { DeviceTable } from './components/DeviceTable'; 

function App() {
  const [data, setData] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');

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
    fetchData(); 
    const interval = setInterval(fetchData, 2000); 
    return () => clearInterval(interval);
  }, []);

  if (!data) return <div className="p-10 text-gray-600">Loading System Data...</div>;

  const { networkOverview, devices } = data;
  
  const atRiskCount = networkOverview.devicesAtRisk; 
  const warningCount = devices.filter(d => d.status === 'Warning').length;

  const renderContent = () => {
    switch (currentView) {
      case 'alerts':
        return <Alerts devices={devices} />;
      case 'dashboard':
      default:
        return (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Network Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <StatCard icon="🛡️" title="Avg Trust Score" value={networkOverview.avgTrustScore} type="success" />
                <StatCard icon="⚠️" title="Devices at Risk" value={networkOverview.devicesAtRisk} type="warning" />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <DeviceTable devices={devices} />
              </div>
              
              <div className="space-y-6">
                 <div className="bg-white p-4 rounded shadow-sm">
                   <h3 className="font-bold text-gray-700">System Status</h3>
                   <p className="text-sm text-gray-500 mt-2">Listening for network traffic...</p>
                   <div className="mt-4 text-xs font-mono text-gray-400 opacity-80">
                      {devices.map(d => (
                        <div key={d.id} className="truncate whitespace-nowrap">
                           [{new Date().toLocaleTimeString()}] update: {d.id}
                        </div>
                      )).slice(0, 8)}
                   </div>
                 </div>
              </div>
            </div>
          </>
        );
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      <Sidebar 
        onNavigate={setCurrentView} 
        currentView={currentView} 
        atRiskCount={atRiskCount} 
        warningCount={warningCount}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}
export default App;