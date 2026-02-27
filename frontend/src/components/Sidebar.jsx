import React from "react";

export function Sidebar({ onNavigate, currentView, atRiskCount, warningCount }) {
  // Tailwind classes used in the sidebar tabs
  const baseNavClasses = "w-full flex items-center px-4 py-2 rounded-md transition-colors duration-200 text-left";
  const getNavActiveClasses = (view) => currentView === view ? "bg-gray-700 text-white" : "text-gray-300 hover:bg-gray-700 hover:text-white";

  return (
    <div className="bg-gray-800 text-white w-64 flex flex-col">
      <div className="h-16 flex items-center pl-6 text-xl font-semibold border-b border-gray-700">
        <span className="text-blue-400">🛡️</span>
        <span>TMS</span>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        <button type="button" onClick={() => onNavigate("dashboard")} className={`${baseNavClasses} ${getNavActiveClasses("dashboard")}`}>
          Dashboard
        </button>
        <button type="button" onClick={() => onNavigate("alerts")} className={`${baseNavClasses} ${getNavActiveClasses("alerts")} justify-between`}>
          <span>Alerts</span>
          {/* Badge counts */}
          <div className="flex gap-2">
            {warningCount > 0 && (
              <span className="bg-yellow-500 text-xs font-bold px-2 py-0.5 rounded-full" title="Warnings">
                {warningCount}
              </span>
            )}
            {atRiskCount > 0 && (
              <span className="bg-red-500 text-xs font-bold px-2 py-0.5 rounded-full" title="At Risk">
                {atRiskCount}
              </span>
              )}
            </div>
        </button>
      </nav>
    </div>
  );
}
