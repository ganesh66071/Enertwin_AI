import type { EnergyRow } from '@/lib/energy-analytics'

export type EnergyProfile = ReturnType<typeof buildEnergyProfile>

const aliases: Record<string, string[]> = {
  recordedAt: ['recorded_at', 'timestamp', 'datetime', 'date', 'time'],
  buildingName: ['building_name', 'building', 'asset', 'site'],
  energyKwh: ['energy_kwh', 'energy', 'consumption', 'kwh'],
  cost: ['cost', 'energy_cost', 'bill'],
  carbonKg: ['carbon_kg', 'carbon', 'co2', 'co2_kg'],
  occupancy: ['occupancy', 'occupancy_percent', 'people', 'load_factor'],
  temperature: ['temperature', 'temp', 'outdoor_temp'],
}

const key = (value: string) => value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '_')
const numeric = (value: unknown, fallback = 0) => { const parsed = Number(String(value ?? '').replace(/[^0-9.-]/g, '')); return Number.isFinite(parsed) ? parsed : fallback }

export function mapEnergyRows(headers: string[], values: string[][]) {
  const normalized = headers.map(key)
  const findIndex = (field: keyof typeof aliases) => normalized.findIndex(header => aliases[field].includes(header))
  const indexes = { recordedAt: findIndex('recordedAt'), buildingName: findIndex('buildingName'), energyKwh: findIndex('energyKwh'), cost: findIndex('cost'), carbonKg: findIndex('carbonKg'), occupancy: findIndex('occupancy'), temperature: findIndex('temperature') }
  const warnings: string[] = []
  if (indexes.recordedAt < 0) warnings.push('Missing timestamp column; rows use the import date.')
  if (indexes.energyKwh < 0) warnings.push('Missing energy column; rows with no energy value were skipped.')
  const rows = values.map((row, index): EnergyRow | null => { const energyKwh = numeric(row[indexes.energyKwh]); if (energyKwh <= 0) return null; const recordedAt = indexes.recordedAt >= 0 && row[indexes.recordedAt] ? row[indexes.recordedAt] : new Date().toISOString(); const buildingName = indexes.buildingName >= 0 && row[indexes.buildingName] ? row[indexes.buildingName] : 'Campus meter'; return { recordedAt, buildingName, energyKwh, cost: numeric(row[indexes.cost], energyKwh * 0.18), carbonKg: numeric(row[indexes.carbonKg], energyKwh * 0.42), occupancy: Math.max(0, numeric(row[indexes.occupancy])), temperature: numeric(row[indexes.temperature], 20) } }).filter(Boolean) as EnergyRow[]
  return { rows, warnings, detected: { timestamp: indexes.recordedAt >= 0, building: indexes.buildingName >= 0, energy: indexes.energyKwh >= 0, cost: indexes.cost >= 0, carbon: indexes.carbonKg >= 0, occupancy: indexes.occupancy >= 0, temperature: indexes.temperature >= 0 } }
}

export function buildEnergyProfile(rows: EnergyRow[]) {
  const total = rows.reduce((sum, row) => sum + row.energyKwh, 0)
  const cost = rows.reduce((sum, row) => sum + row.cost, 0)
  const carbon = rows.reduce((sum, row) => sum + row.carbonKg, 0)
  const byBuilding = Object.values(rows.reduce<Record<string, { name: string; energy: number; readings: number }>>((acc, row) => { const item = acc[row.buildingName] || { name: row.buildingName, energy: 0, readings: 0 }; item.energy += row.energyKwh; item.readings += 1; acc[row.buildingName] = item; return acc }, {})).sort((a, b) => b.energy - a.energy).map(item => ({ ...item, share: total ? item.energy / total : 0 }))
  const peak = rows.reduce((max, row) => row.energyKwh > (max?.energyKwh || 0) ? row : max, rows[0])
  const average = rows.length ? total / rows.length : 0
  const baseline = total * 1.12
  return { rows, hasData: rows.length > 0, source: rows.length ? 'dataset' as const : 'empty' as const, totalEnergyKwh: total, totalCost: cost, totalCarbonKg: carbon, averageOccupancy: rows.length ? rows.reduce((sum, row) => sum + row.occupancy, 0) / rows.length : 0, baselineKwh: baseline, savingsKwh: Math.max(0, baseline - total), savingsPercent: baseline ? (baseline - total) / baseline : 0, peak: peak ? { value: peak.energyKwh, building: peak.buildingName, recordedAt: peak.recordedAt } : null, byBuilding, score: rows.length ? Math.max(0, Math.min(100, Math.round(100 - (average / Math.max(average, 1)) * 18))) : 0 }
}

export function deriveSimulationBaseline(profile: EnergyProfile) { return { baselineKwh: profile.totalEnergyKwh, peakKwh: profile.peak?.value || 0, occupancy: profile.averageOccupancy, carbonKg: profile.totalCarbonKg, buildingCount: profile.byBuilding.length } }
