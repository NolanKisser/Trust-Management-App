export const mockData = {
  networkOverview: {
    avgTrustScore: 0.82,
    devicesAtRisk: 3,
    activeGateways: 4,
  },
  gateways: [
    { id: 'A', name: 'Gateway A', devices: 12, status: 'Suspect', score: 0.76 },
    { id: 'B', name: 'Gateway B', devices: 8, status: 'OK', score: 0.92 },
    { id: 'C', name: 'Gateway C', devices: 6, status: 'OK', score: 0.88 },
    { id: 'D', name: 'Gateway D', devices: 5, status: 'OK', score: 0.80 },
  ],
  alerts: [
    { id: 1, title: 'ON-OFF Attack Detected', device: 'Device D-102', time: '5 min ago' },
    { id: 2, title: 'ON-OFF Attack Detected', device: 'Device D-102', time: '20 min ago' },
  ],
  devices: [
    { id: 'D-101', trustScore: 0.91, status: 'Normal', lastSeen: '2s ago', profile: 'Profile 9' },
    { id: 'D-102', trustScore: 0.43, status: 'At Risk', lastSeen: '10s ago', profile: 'Profile 21' },
    { id: 'D-103', trustScore: 0.78, status: 'Warning', lastSeen: '4s ago', profile: 'Profile 10' },
  ],
};