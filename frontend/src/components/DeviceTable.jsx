import React, { useEffect, useMemo, useState } from 'react';

const MAX_CURRENT_JITTER = 0.05;
const JITTER_STEP = 0.01;
const JITTER_INTERVAL_MS = 300;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const parseTrustDisplay = (trustDisplay) => {
  if (!trustDisplay) return null;
  const match = trustDisplay.match(/^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)(.*\|\s*(?:Current|Last):\s*)(-?\d+(?:\.\d+)?)(.*)$/);
  if (!match) return null;

  const lowerBound = Number(match[1]);
  const upperBound = Number(match[2]);
  return {
    lowerBound: Math.min(lowerBound, upperBound),
    upperBound: Math.max(lowerBound, upperBound),
    prefix: `${match[1]} - ${match[2]}${match[3]}`,
    current: Number(match[4]),
    suffix: match[5] || '',
  };
};

export function DeviceTable({ devices, onDeviceClick, darkMode }) {
  const [fluctuatingCurrentByDevice, setFluctuatingCurrentByDevice] = useState({});
  const [classSortDirection, setClassSortDirection] = useState('asc');

  useEffect(() => {
    setFluctuatingCurrentByDevice((previous) => {
      const next = {};

      devices.forEach((device) => {
        const parsed = parseTrustDisplay(device.trustDisplay);
        if (!parsed || Number.isNaN(parsed.current)) return;

        const existing = previous[device.id];
        if (existing && Math.abs(existing.base - parsed.current) < 0.0001) {
          next[device.id] = existing;
          return;
        }

        next[device.id] = {
          base: parsed.current,
          value: clamp(parsed.current, parsed.lowerBound, parsed.upperBound),
          lowerBound: parsed.lowerBound,
          upperBound: parsed.upperBound,
        };
      });

      return next;
    });
  }, [devices]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setFluctuatingCurrentByDevice((previous) => {
        const next = {};

        Object.entries(previous).forEach(([deviceId, state]) => {
          const drift = (Math.random() * 2 - 1) * JITTER_STEP;
          const minAllowed = Math.max(state.base - MAX_CURRENT_JITTER, state.lowerBound, 0);
          const maxAllowed = Math.min(state.base + MAX_CURRENT_JITTER, state.upperBound, 1);
          const nextValue = clamp(state.value + drift, minAllowed, maxAllowed);

          next[deviceId] = { ...state, value: nextValue };
        });

        return next;
      });
    }, JITTER_INTERVAL_MS);

    return () => clearInterval(intervalId);
  }, []);

  const getAnimatedTrustDisplay = (device) => {
    const fallback = device.trustDisplay || "Calculating...";
    const parsed = parseTrustDisplay(device.trustDisplay);
    if (!parsed) return fallback;

    const jitterState = fluctuatingCurrentByDevice[device.id];
    if (!jitterState) return fallback;

    return `${parsed.prefix}${jitterState.value.toFixed(2)}${parsed.suffix}`;
  };

  const getStatusClass = (status) => {
    if (darkMode) {
      switch (status) {
        case 'Normal': return 'bg-emerald-900/50 text-emerald-200';
        case 'At Risk': return 'bg-red-900/50 text-red-200';
        case 'Warning': return 'bg-amber-900/50 text-amber-200';
        default: return 'bg-slate-800 text-slate-200';
      }
    }
    switch (status) {
      case 'Normal': return 'bg-green-100 text-green-800';
      case 'At Risk': return 'bg-red-100 text-red-800';
      case 'Warning': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getClassRank = (profile) => {
    const match = (profile || '').match(/class\s+(\d+)/i);
    if (!match) return Number.POSITIVE_INFINITY;
    return Number(match[1]);
  };

  const sortedDevices = useMemo(() => {
    const direction = classSortDirection === 'asc' ? 1 : -1;
    return [...devices].sort((a, b) => {
      const classDiff = (getClassRank(a.profile) - getClassRank(b.profile)) * direction;
      if (classDiff !== 0) return classDiff;
      return a.id.localeCompare(b.id);
    });
  }, [devices, classSortDirection]);

  const toggleClassSort = () => {
    setClassSortDirection((previous) => (previous === 'asc' ? 'desc' : 'asc'));
  };

  return (
    <div className={`rounded-lg shadow-sm overflow-hidden border ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-200'}`}>
      <div className={`px-6 py-4 border-b flex justify-between items-center ${darkMode ? 'border-slate-700' : 'border-gray-200'}`}>
        <h2 className={`font-semibold text-lg ${darkMode ? 'text-slate-100' : 'text-gray-800'}`}>Connected Devices</h2>
        <span className={`text-xs font-mono ${darkMode ? 'text-slate-400' : 'text-gray-400'}`}>Real-time update active</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className={`${darkMode ? 'bg-slate-800 text-slate-300' : 'bg-gray-50 text-gray-600'} text-xs uppercase font-bold tracking-wider`}>
            <tr>
              <th className="px-6 py-4">Device ID</th>
              <th className="px-6 py-4">Trust Score</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">
                <button
                  type="button"
                  onClick={toggleClassSort}
                  className={`inline-flex items-center gap-1 transition-colors ${darkMode ? 'hover:text-white' : 'hover:text-gray-900'}`}
                  title={`Sort by class (${classSortDirection === 'asc' ? 'ascending' : 'descending'})`}
                >
                  Profile / Classification
                  <span aria-hidden="true">{classSortDirection === 'asc' ? '↑' : '↓'}</span>
                </button>
              </th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className={`divide-y text-sm ${darkMode ? 'divide-slate-700 text-slate-200' : 'divide-gray-200 text-gray-700'}`}>
            {sortedDevices.map((device) => (
              <tr key={device.id} className={`transition-colors ${darkMode ? 'hover:bg-slate-800' : 'hover:bg-gray-50'}`}>
                <td className={`px-6 py-4 font-semibold cursor-pointer ${darkMode ? 'text-blue-300 hover:text-blue-200' : 'text-blue-600'}`} onClick={() => onDeviceClick(device)}>
                  {device.id}
                </td>
                <td className="px-6 py-4">
                  <span className={`font-mono font-medium px-2 py-1 rounded ${darkMode ? 'text-slate-200 bg-slate-800' : 'text-gray-600 bg-gray-100'}`}>
                    {getAnimatedTrustDisplay(device)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${getStatusClass(device.status)}`}>
                    {device.status}
                  </span>
                </td>
                <td className={`px-6 py-4 font-medium italic ${darkMode ? 'text-slate-300' : 'text-gray-600'}`}>
                    {device.profile || "Waiting..."}
                </td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => onDeviceClick(device)}
                    className={`text-xs px-3 py-1.5 rounded-md transition-all font-semibold border ${
                      darkMode
                        ? 'bg-slate-800 text-slate-200 border-slate-600 hover:bg-slate-700 hover:text-white'
                        : 'bg-blue-50 text-blue-600 border-blue-100 hover:bg-blue-600 hover:text-white'
                    }`}
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