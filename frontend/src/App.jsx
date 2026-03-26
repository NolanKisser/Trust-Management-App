import React, { useState, useEffect } from 'react';
import './App.css'; 
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { StatCard } from './components/StatCard';
import { Alerts } from './components/Alerts';
import { DeviceTable } from './components/DeviceTable'; 
import LLMAnalysis from './components/LLMAnalysis'; // 1. Added Import

function App() {
  const [data, setData] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedDevice, setSelectedDevice] = useState(null); // 2. State for LLM context
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('tms-theme');
    if (savedTheme === 'dark') setDarkMode(true);
  }, []);

  useEffect(() => {
    localStorage.setItem('tms-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

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

  if (!data) return <div className={`p-10 ${darkMode ? 'text-slate-300 bg-slate-950 min-h-screen' : 'text-gray-600 bg-gray-100 min-h-screen'}`}>Loading System Data...</div>;

  const { networkOverview, devices, aiEngineModel } = data;
  
  const atRiskCount = networkOverview.devicesAtRisk; 
  const warningCount = devices.filter(d => d.status === 'Warning').length;

  // Helper to switch to LLM view when a device is clicked
  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
    setCurrentView('llm-analysis');
  };

  const renderContent = () => {
    switch (currentView) {
      case 'alerts':
        return <Alerts devices={devices} darkMode={darkMode} />;
      
      case 'llm-analysis': // 3. Added LLM Analysis View
        return (
          <div className="flex h-full gap-6">
            <div className="w-1/3 space-y-4 overflow-y-auto">
              <h2 className={`text-xl font-semibold ${darkMode ? 'text-slate-100' : 'text-gray-800'}`}>Select Device</h2>
              {devices.map(d => (
                <div 
                  key={d.id} 
                  onClick={() => setSelectedDevice(d)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedDevice?.id === d.id 
                    ? darkMode
                      ? 'bg-blue-900/60 text-blue-50 border-blue-700 shadow-sm'
                      : 'bg-blue-600 text-white border-blue-600 shadow-md'
                    : darkMode
                      ? 'bg-slate-800 text-slate-200 border-slate-700 hover:border-blue-400'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-blue-400'
                  }`}
                >
                  <div className="font-bold">{d.id}</div>
                  <div className={`text-xs ${selectedDevice?.id === d.id ? 'text-blue-100' : darkMode ? 'text-slate-400' : 'text-gray-500'}`}>
                    Status: {d.status} | Profile: {d.profile}
                  </div>
                </div>
              ))}
            </div>
            <div className={`flex-1 rounded-lg shadow-sm border overflow-hidden flex flex-col ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-200'}`}>
              {selectedDevice ? (
                <LLMAnalysis key={selectedDevice.id} selectedDevice={selectedDevice} darkMode={darkMode} />
              ) : (
                <div className={`flex flex-col items-center justify-center h-full p-10 text-center ${darkMode ? 'text-slate-400' : 'text-gray-400'}`}>
                  <span className="text-5xl mb-4">🧠</span>
                  <p>Select a device from the left to begin AI-powered behavioral analysis.</p>
                </div>
              )}
            </div>
          </div>
        );

      case 'dashboard':
      default:
        return (
          <>
            <div className="mb-6">
              <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-slate-100' : 'text-gray-800'}`}>Network Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <StatCard icon="🛡️" title="Avg Trust Score" value={networkOverview.avgTrustScore} type="success" darkMode={darkMode} />
                <StatCard icon="⚠️" title="Devices at Risk" value={networkOverview.devicesAtRisk} type="warning" darkMode={darkMode} />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* 4. Pass selection handler to table */}
                <DeviceTable devices={devices} onDeviceClick={handleDeviceSelect} darkMode={darkMode} />
              </div>
              
              <div className="space-y-6">
                 <div className={`p-4 rounded shadow-sm border ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-200'}`}>
                   <h3 className={`font-bold ${darkMode ? 'text-slate-100' : 'text-gray-700'}`}>System Status</h3>
                   <p className={`text-sm mt-2 ${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>Listening for network traffic...</p>
                   <div className={`mt-4 text-xs font-mono opacity-80 ${darkMode ? 'text-slate-500' : 'text-gray-400'}`}>
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
    <div className={`flex h-screen overflow-hidden ${darkMode ? 'bg-slate-950' : 'bg-gray-100'}`}>
      <Sidebar 
        onNavigate={setCurrentView} 
        currentView={currentView} 
        atRiskCount={atRiskCount} 
        warningCount={warningCount}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode((previous) => !previous)}
        aiEngineModel={aiEngineModel}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar darkMode={darkMode} />
        <main className={`flex-1 overflow-x-hidden overflow-y-auto p-6 ${darkMode ? 'bg-slate-950' : 'bg-gray-100'}`}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;