export type EnergyRow = { recordedAt: string; buildingName: string; energyKwh: number; cost: number; carbonKg: number; occupancy: number; temperature: number }

const number = (value: unknown) => Number(value || 0)

export function processEnergyAnalytics(rows: EnergyRow[]) {
  const totalEnergy = rows.reduce((sum, row) => sum + number(row.energyKwh), 0)
  const totalCost = rows.reduce((sum, row) => sum + number(row.cost), 0)
  const totalCarbon = rows.reduce((sum, row) => sum + number(row.carbonKg), 0)
  const averageOccupancy = rows.length ? rows.reduce((sum, row) => sum + number(row.occupancy), 0) / rows.length : 0
  const byBuilding = Object.entries(rows.reduce<Record<string, { buildingName: string; energyKwh: number; cost: number; carbonKg: number; readings: number }>>((map, row) => { const current = map[row.buildingName] || { buildingName: row.buildingName, energyKwh: 0, cost: 0, carbonKg: 0, readings: 0 }; current.energyKwh += number(row.energyKwh); current.cost += number(row.cost); current.carbonKg += number(row.carbonKg); current.readings += 1; map[row.buildingName] = current; return map }, {})).map(([, value]) => ({ ...value, energyKwh: Math.round(value.energyKwh * 10) / 10, share: totalEnergy ? Math.round((value.energyKwh / totalEnergy) * 1000) / 10 : 0 })).sort((a, b) => b.energyKwh - a.energyKwh)
  const byDay = Object.entries(rows.reduce<Record<string, number>>((map, row) => { const day = String(row.recordedAt).slice(0, 10); map[day] = (map[day] || 0) + number(row.energyKwh); return map }, {})).map(([date, energyKwh]) => ({ date, energyKwh: Math.round(energyKwh * 10) / 10 })).slice(-30)
  const byHour = Array.from({ length: 24 }, (_, hour) => { const matching = rows.filter(row => new Date(row.recordedAt).getHours() === hour); return { hour: `${String(hour).padStart(2, '0')}:00`, energyKwh: matching.length ? Math.round((matching.reduce((sum, row) => sum + number(row.energyKwh), 0) / matching.length) * 10) / 10 : 0 } })
  const peak = rows.reduce((max, row) => number(row.energyKwh) > number(max?.energyKwh) ? row : max, rows[0])
  const baseline = totalEnergy * 1.12
  const savings = Math.max(0, baseline - totalEnergy)
  const anomalyThreshold = rows.length ? totalEnergy / rows.length * 1.65 : 0
  const anomalies = rows.filter(row => number(row.energyKwh) > anomalyThreshold).slice(-12).map(row => ({ ...row, severity: number(row.energyKwh) > anomalyThreshold * 1.35 ? 'critical' : 'warning' }))
  return { hasData: rows.length > 0, readings: rows.length, totalEnergy: Math.round(totalEnergy * 10) / 10, totalCost: Math.round(totalCost * 100) / 100, totalCarbon: Math.round(totalCarbon * 10) / 10, averageOccupancy: Math.round(averageOccupancy * 10) / 10, baseline: Math.round(baseline * 10) / 10, savings: Math.round(savings * 10) / 10, savingsPercent: baseline ? Math.round((savings / baseline) * 1000) / 10 : 0, peak: peak ? { value: number(peak.energyKwh), at: peak.recordedAt, buildingName: peak.buildingName } : null, byBuilding, byDay, byHour, anomalies, score: rows.length ? Math.max(0, Math.min(100, Math.round(100 - (totalEnergy / baseline) * 22 - anomalies.length * 2))) : 0 }
}

export const emptyAnalytics = processEnergyAnalytics([])
