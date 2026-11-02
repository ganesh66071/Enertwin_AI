export type AnomalySeverity = 'critical' | 'warning' | 'info'

export interface Anomaly {
  id: string
  title: string
  building: string
  buildingId: string
  system: string
  asset: string
  severity: AnomalySeverity
  detected: string
  time: string
  current: string
  expected: string
  deviation: string
  confidence: number
  description: string
}

export const anomalyData: Anomaly[] = [
  { id: 'hvac-07', title: 'Unexpected energy consumption spike', building: 'Mechanical Block', buildingId: 'mechanical-block', system: 'HVAC System', asset: 'HVAC-07', severity: 'critical', detected: '2 minutes ago', time: '14:32', current: '58.4 kW', expected: '42.1 kW', deviation: '+38.7%', confidence: 97, description: 'Cooling demand is materially above the learned operating envelope for the current occupancy and weather conditions.' },
  { id: 'ahu-04', title: 'Air handling unit running after occupancy', building: 'Innovation Centre', buildingId: 'ece-block', system: 'Air handling', asset: 'AHU-04', severity: 'warning', detected: '18 minutes ago', time: '14:16', current: '24.1 kW', expected: '11.8 kW', deviation: '+104%', confidence: 91, description: 'The unit is still serving an unoccupied zone after the scheduled learning window.' },
  { id: 'lighting-b', title: 'Lighting circuit above baseline', building: 'Library & Archive', buildingId: 'library', system: 'Lighting', asset: 'Circuit B', severity: 'warning', detected: '41 minutes ago', time: '13:53', current: '8.7 kW', expected: '5.4 kW', deviation: '+61%', confidence: 88, description: 'Lighting load remains high despite lower observed occupancy in the west reading room.' },
  { id: 'chiller-02', title: 'Chiller efficiency improving', building: 'North Residence', buildingId: 'cse-block', system: 'Chiller plant', asset: 'Chiller-02', severity: 'info', detected: '1 hour ago', time: '13:12', current: '0.61 kW/RT', expected: '0.72 kW/RT', deviation: '-15%', confidence: 84, description: 'Recent control changes are performing better than the expected seasonal model.' },
]

export const buildingOverview = [
  { name: 'Mechanical Block', id: 'mechanical-block', anomalies: 3, efficiency: 82, status: 'critical', color: '#ef4444' },
  { name: 'Innovation Centre', id: 'ece-block', anomalies: 2, efficiency: 91, status: 'warning', color: '#f59e0b' },
  { name: 'North Residence', id: 'cse-block', anomalies: 1, efficiency: 96, status: 'healthy', color: '#10b981' },
  { name: 'Library & Archive', id: 'library', anomalies: 0, efficiency: 94, status: 'healthy', color: '#10b981' },
]

export const anomalyChartData = {
  '24H': [
    { time: '00:00', expected: 32, actual: 30 }, { time: '04:00', expected: 28, actual: 29 }, { time: '08:00', expected: 45, actual: 51 },
    { time: '12:00', expected: 48, actual: 54 }, { time: '14:00', expected: 44, actual: 61 }, { time: '16:00', expected: 46, actual: 58 }, { time: '20:00', expected: 38, actual: 41 },
  ],
  '7D': [
    { time: 'Mon', expected: 310, actual: 326 }, { time: 'Tue', expected: 298, actual: 304 }, { time: 'Wed', expected: 322, actual: 349 },
    { time: 'Thu', expected: 315, actual: 338 }, { time: 'Fri', expected: 330, actual: 356 }, { time: 'Sat', expected: 190, actual: 198 }, { time: 'Sun', expected: 172, actual: 182 },
  ],
  '30D': [
    { time: 'W1', expected: 1880, actual: 1940 }, { time: 'W2', expected: 1920, actual: 1974 }, { time: 'W3', expected: 2010, actual: 2110 }, { time: 'W4', expected: 1980, actual: 2168 },
  ],
}
