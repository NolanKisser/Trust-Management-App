import React, { useEffect, useMemo, useState } from 'react';

const chartWidth = 920;
const chartHeight = 320;
const padding = { top: 20, right: 20, bottom: 42, left: 48 };
const Y_MIN = 0;
const Y_MAX = 1;

const parseTrustFromDisplay = (trustDisplay) => {
  if (!trustDisplay) return [];
  const match = trustDisplay.match(/\|\s*Current:\s*(-?\d+(?:\.\d+)?)/i);
  if (!match) return [];
  const current = Number(match[1]);
  return Number.isNaN(current) ? [] : [current];
};

const formatDateTime = (value) => {
  if (!value) return 'N/A';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'N/A';
  return date.toLocaleString();
};

export function TrustTimeline({ devices, darkMode }) {
  const [selectedId, setSelectedId] = useState(devices[0]?.id || null);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [showAttributeLine, setShowAttributeLine] = useState(false);
  const [selectedAttribute, setSelectedAttribute] = useState('networkDelay');

  useEffect(() => {
    if (!devices.length) {
      setSelectedId(null);
      return;
    }
    const stillExists = devices.some((device) => device.id === selectedId);
    if (!stillExists) {
      setSelectedId(devices[0].id);
    }
  }, [devices, selectedId]);

  const selectedDevice = useMemo(
    () => devices.find((device) => device.id === selectedId) || null,
    [devices, selectedId]
  );

  const trustValues = selectedDevice?.trustSeries?.length
    ? selectedDevice.trustSeries
    : parseTrustFromDisplay(selectedDevice?.trustDisplay);
  const attributeLabelMap = {
    networkDelay: 'Network Delay',
    interactionHistory: 'Interaction History',
    networkThroughput: 'Network Throughput',
  };
  const allowedOverlayKeys = [
    'networkDelay',
    'interactionHistory',
    'networkThroughput',
  ];
  const attributeKeys = allowedOverlayKeys.filter(
    (key) => (selectedDevice?.attributeSeries?.[key] || []).length > 0
  );

  useEffect(() => {
    if (!selectedDevice) return;
    if (!attributeKeys.length) {
      setShowAttributeLine(false);
      return;
    }
    if (!attributeKeys.includes(selectedAttribute)) {
      setSelectedAttribute(attributeKeys[0]);
    }
  }, [selectedDevice, attributeKeys, selectedAttribute]);

  const selectedAttributeValues = showAttributeLine
    ? selectedDevice?.attributeSeries?.[selectedAttribute] || []
    : [];
  const normalizedAttributeValues = useMemo(() => {
    if (!selectedAttributeValues.length) return [];
    const min = Math.min(...selectedAttributeValues);
    const max = Math.max(...selectedAttributeValues);
    if (Math.abs(max - min) < 0.000001) {
      return selectedAttributeValues.map(() => 0.5);
    }
    return selectedAttributeValues.map((value) => (value - min) / (max - min));
  }, [selectedAttributeValues]);

  const elapsedSecondsEnd = Math.max(0, trustValues.length - 1);
  const timeGridStep = elapsedSecondsEnd <= 120 ? 10 : 50;
  const gridTickSeconds = useMemo(() => {
    if (elapsedSecondsEnd <= 0) return [0];
    const ticks = [];
    for (let second = 0; second <= elapsedSecondsEnd; second += timeGridStep) {
      ticks.push(second);
    }
    if (ticks[ticks.length - 1] !== elapsedSecondsEnd) {
      ticks.push(elapsedSecondsEnd);
    }
    return ticks;
  }, [elapsedSecondsEnd, timeGridStep]);
  const yTicks = useMemo(
    () => Array.from({ length: 11 }, (_, index) => Number((Y_MAX - index * 0.1).toFixed(1))),
    []
  );
  const drawableWidth = chartWidth - padding.left - padding.right;
  const drawableHeight = chartHeight - padding.top - padding.bottom;

  const buildPolylinePoints = (seriesValues) => {
    if (!seriesValues?.length) return '';
    return seriesValues.map((value, index) => {
      const x = padding.left + (index / Math.max(1, seriesValues.length - 1)) * drawableWidth;
      const clamped = Math.min(Math.max(Number(value), Y_MIN), Y_MAX);
      const y = padding.top + (1 - (clamped - Y_MIN) / (Y_MAX - Y_MIN)) * drawableHeight;
      return `${x},${y}`;
    }).join(' ');
  };

  const { points, attributePoints } = useMemo(() => {
    if (!trustValues?.length) {
      return { points: '', attributePoints: '' };
    }
    return {
      points: buildPolylinePoints(trustValues),
      attributePoints: buildPolylinePoints(
        normalizedAttributeValues.slice(0, trustValues.length)
      ),
    };
  }, [trustValues, normalizedAttributeValues, drawableWidth, drawableHeight]);

  const axisColor = darkMode ? '#64748b' : '#94a3b8';
  const textColorClass = darkMode ? 'text-slate-200' : 'text-gray-700';
  const hoveredValue =
    hoveredIndex !== null && trustValues[hoveredIndex] !== undefined
      ? Math.min(Math.max(Number(trustValues[hoveredIndex]), Y_MIN), Y_MAX)
      : null;
  const hoveredX =
    hoveredIndex !== null
      ? padding.left + (hoveredIndex / Math.max(1, trustValues.length - 1)) * drawableWidth
      : null;
  const hoveredY =
    hoveredValue !== null
      ? padding.top + (1 - (hoveredValue - Y_MIN) / (Y_MAX - Y_MIN)) * drawableHeight
      : null;

  const handleChartMouseMove = (event) => {
    if (!trustValues.length) return;
    const svgRect = event.currentTarget.getBoundingClientRect();
    const relativeX = ((event.clientX - svgRect.left) / svgRect.width) * chartWidth;
    const clampedX = Math.min(Math.max(relativeX, padding.left), chartWidth - padding.right);
    const ratio = (clampedX - padding.left) / drawableWidth;
    const nearestIndex = Math.round(ratio * Math.max(1, trustValues.length - 1));
    setHoveredIndex(Math.min(Math.max(nearestIndex, 0), trustValues.length - 1));
  };

  return (
    <div className={`rounded-lg shadow-sm border ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-gray-200'}`}>
      <div className={`px-6 py-4 border-b flex flex-col gap-3 ${darkMode ? 'border-slate-700' : 'border-gray-200'}`}>
        <h2 className={`text-lg font-semibold ${darkMode ? 'text-slate-100' : 'text-gray-800'}`}>Trust Over Time</h2>
        <div className="flex flex-wrap items-center gap-3">
          <label htmlFor="timeline-device-select" className={`text-sm ${textColorClass}`}>
            Device
          </label>
          <select
            id="timeline-device-select"
            value={selectedId || ''}
            onChange={(event) => setSelectedId(event.target.value)}
            className={`px-3 py-2 rounded-md border text-sm ${
              darkMode
                ? 'bg-slate-800 border-slate-600 text-slate-100'
                : 'bg-white border-gray-300 text-gray-700'
            }`}
          >
            {devices.map((device) => (
              <option key={device.id} value={device.id}>
                {device.id}
              </option>
            ))}
          </select>

          <label className={`inline-flex items-center gap-2 text-sm ${textColorClass}`}>
            <input
              type="checkbox"
              checked={showAttributeLine}
              onChange={(event) => setShowAttributeLine(event.target.checked)}
              disabled={!attributeKeys.length}
            />
            Compare attribute
          </label>
          <select
            value={selectedAttribute}
            onChange={(event) => setSelectedAttribute(event.target.value)}
            disabled={!showAttributeLine || !attributeKeys.length}
            className={`px-3 py-2 rounded-md border text-sm ${
              darkMode
                ? 'bg-slate-800 border-slate-600 text-slate-100 disabled:opacity-50'
                : 'bg-white border-gray-300 text-gray-700 disabled:opacity-50'
            }`}
          >
            {attributeKeys.map((key) => (
              <option key={key} value={key}>
                {attributeLabelMap[key] || key}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="p-6">
        {!selectedDevice ? (
          <div className={`${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>No device data available yet.</div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
              <div className={`rounded-md px-3 py-2 text-sm ${darkMode ? 'bg-slate-800 text-slate-200' : 'bg-gray-50 text-gray-700'}`}>
                Initiated: <span className="font-medium">{formatDateTime(selectedDevice.initiatedAt)}</span>
              </div>
              <div className={`rounded-md px-3 py-2 text-sm ${darkMode ? 'bg-slate-800 text-slate-200' : 'bg-gray-50 text-gray-700'}`}>
                Graph End: <span className="font-medium">{formatDateTime(selectedDevice.graphEndAt)}</span>
              </div>
              <div className={`rounded-md px-3 py-2 text-sm ${darkMode ? 'bg-slate-800 text-slate-200' : 'bg-gray-50 text-gray-700'}`}>
                Samples: <span className="font-medium">{selectedDevice.timelineLength || trustValues.length}</span>
              </div>
            </div>

            {trustValues.length > 0 ? (
              <div className={`rounded-md p-3 ${darkMode ? 'bg-slate-950' : 'bg-slate-50'}`}>
                <svg
                  viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                  role="img"
                  aria-label={`Trust score over time for ${selectedDevice.id}`}
                  className="w-full h-auto"
                  onMouseMove={handleChartMouseMove}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  {yTicks.map((tick) => {
                    const ratio = (tick - Y_MIN) / (Y_MAX - Y_MIN);
                    const y = padding.top + (1 - ratio) * (chartHeight - padding.top - padding.bottom);
                    return (
                      <g key={`y-tick-${tick}`}>
                        <line
                          x1={padding.left}
                          y1={y}
                          x2={chartWidth - padding.right}
                          y2={y}
                          stroke={axisColor}
                          strokeOpacity="0.2"
                          strokeDasharray="3 4"
                        />
                        <text x={12} y={y + 4} fontSize="11" fill={axisColor}>
                          {tick.toFixed(1)}
                        </text>
                      </g>
                    );
                  })}

                  {gridTickSeconds.map((second) => {
                    const ratio = elapsedSecondsEnd === 0 ? 0 : second / elapsedSecondsEnd;
                    const x = padding.left + ratio * (chartWidth - padding.left - padding.right);
                    return (
                      <g key={`tick-${second}`}>
                        <line
                          x1={x}
                          y1={padding.top}
                          x2={x}
                          y2={chartHeight - padding.bottom}
                          stroke={axisColor}
                          strokeOpacity="0.25"
                          strokeDasharray="4 4"
                        />
                        <text
                          x={x}
                          y={chartHeight - 16}
                          fontSize="11"
                          fill={axisColor}
                          textAnchor="middle"
                        >
                          {second}s
                        </text>
                      </g>
                    );
                  })}

                  <line x1={padding.left} y1={padding.top} x2={padding.left} y2={chartHeight - padding.bottom} stroke={axisColor} />
                  <line x1={padding.left} y1={chartHeight - padding.bottom} x2={chartWidth - padding.right} y2={chartHeight - padding.bottom} stroke={axisColor} />

                  <polyline fill="none" stroke="#3b82f6" strokeWidth="2.5" points={points} />
                  {showAttributeLine && attributePoints && (
                    <polyline fill="none" stroke="#f59e0b" strokeWidth="2.2" points={attributePoints} />
                  )}

                  {hoveredIndex !== null && hoveredX !== null && hoveredY !== null && (
                    <>
                      <line
                        x1={hoveredX}
                        y1={padding.top}
                        x2={hoveredX}
                        y2={chartHeight - padding.bottom}
                        stroke="#3b82f6"
                        strokeOpacity="0.35"
                        strokeDasharray="3 4"
                      />
                      <circle cx={hoveredX} cy={hoveredY} r="4.5" fill="#3b82f6" />
                      <g transform={`translate(${Math.min(hoveredX + 10, chartWidth - 150)},${Math.max(hoveredY - 44, padding.top + 4)})`}>
                        <rect
                          width="140"
                          height="26"
                          rx="6"
                          fill={darkMode ? '#0f172a' : '#ffffff'}
                          stroke={darkMode ? '#334155' : '#cbd5e1'}
                        />
                        <text x="8" y="17" fontSize="11" fill={darkMode ? '#e2e8f0' : '#0f172a'}>
                          trust = {hoveredValue.toFixed(3)}
                        </text>
                      </g>
                    </>
                  )}
                </svg>
              </div>
            ) : (
              <div className={`${darkMode ? 'text-slate-400' : 'text-gray-500'}`}>
                Trust history is not available yet for this device.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
