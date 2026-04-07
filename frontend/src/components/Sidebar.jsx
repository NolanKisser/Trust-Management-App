import React from "react";

export function Sidebar({ onNavigate, currentView, atRiskCount, warningCount, darkMode, onToggleDarkMode, aiEngineModel }) {
  // Tailwind classes used in the sidebar tabs
  const baseNavClasses = "w-full flex items-center px-4 py-2.5 rounded-lg transition-all duration-200 text-left border";
  const getNavActiveClasses = (view) => {
    if (darkMode) {
      return currentView === view
        ? "bg-blue-900/40 text-blue-100 border-blue-700 shadow-sm"
        : "text-slate-300 border-transparent hover:bg-slate-800 hover:text-slate-100";
    }
    return currentView === view
      ? "bg-blue-50 text-blue-700 border-blue-200 shadow-sm"
      : "text-gray-700 border-transparent hover:bg-gray-100 hover:text-gray-900";
  };

  return (
    <div className={`w-72 flex flex-col h-full transition-colors ${darkMode ? "bg-slate-900 text-white border-r border-slate-700" : "bg-white text-gray-900 border-r border-gray-200"}`}>
      <div className={`h-20 flex items-center px-6 ${darkMode ? "border-b border-slate-700" : "border-b border-gray-200"}`}>
        <span className="text-blue-400 mr-2 text-2xl">🛡️</span>
        <div>
          <span className="text-lg font-semibold tracking-tight">TMS</span>
          <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>Intelligent Network Monitoring</p>
        </div>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2.5">
        <button 
          type="button" 
          onClick={() => onNavigate("dashboard")} 
          className={`${baseNavClasses} ${getNavActiveClasses("dashboard")}`}
        >
          <span className="mr-3">📊</span>
          Dashboard
        </button>

        <button 
          type="button" 
          onClick={() => onNavigate("alerts")} 
          className={`${baseNavClasses} ${getNavActiveClasses("alerts")} justify-between`}
        >
          <div className="flex items-center">
            <span className="mr-3">🔔</span>
            <span>Alerts</span>
          </div>
          {/* Badge counts */}
          <div className="flex gap-2">
            {warningCount > 0 && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${darkMode ? 'bg-amber-900/60 text-amber-200' : 'bg-yellow-500 text-white'}`} title="Warnings">
                {warningCount}
              </span>
            )}
            {atRiskCount > 0 && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${darkMode ? 'bg-red-900/60 text-red-200' : 'bg-red-500 text-white'}`} title="At Risk">
                {atRiskCount}
              </span>
            )}
          </div>
        </button>

        {/* New LLM Analysis Tab */}
        <button 
          type="button" 
          onClick={() => onNavigate("llm-analysis")} 
          className={`${baseNavClasses} ${getNavActiveClasses("llm-analysis")}`}
        >
          <span className="mr-3">🧠</span>
          LLM Analysis
        </button>

        <button
          type="button"
          onClick={() => onNavigate("trust-timeline")}
          className={`${baseNavClasses} ${getNavActiveClasses("trust-timeline")}`}
        >
          <span className="mr-3">📈</span>
          Trust Timeline
        </button>
      </nav>

      <div className={`mt-auto p-4 border-t space-y-3 ${darkMode ? "border-slate-700" : "border-gray-200"}`}>
        <button
          type="button"
          onClick={onToggleDarkMode}
          className={`w-full flex items-center justify-between text-xs font-semibold px-3 py-2 rounded-md transition-colors ${
            darkMode
              ? "bg-slate-800 text-slate-200 hover:bg-slate-700"
              : "bg-gray-100 text-gray-800 hover:bg-gray-200"
          }`}
        >
          <span>{darkMode ? "Dark Mode" : "Light Mode"}</span>
          <span>{darkMode ? "🌙" : "☀️"}</span>
        </button>
        <div className={`text-xs ${darkMode ? "text-slate-400" : "text-gray-500"}`}>
          AI Engine: {aiEngineModel || "Unavailable"}
        </div>
      </div>
    </div>
  );
}