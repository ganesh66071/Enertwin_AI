'use client'

import { useEffect, useState } from 'react'
import { getCampuses } from '@/app/actions/campuses'
import { FileSpreadsheet, Upload, Database, CheckCircle2 } from 'lucide-react'
import { addEnergyRecords, seedDemoEnergyData } from '@/app/actions/energy-data'

type Props = { campusId?: string }

export function CampusDataPanel({ campusId: providedCampusId }: Props) {
  const [campusId, setCampusId] = useState(providedCampusId || '')
  const [status, setStatus] = useState('')
  useEffect(() => { if (!providedCampusId) getCampuses().then(items => setCampusId(items[0]?.id || '')).catch(() => undefined) }, [providedCampusId])
  const [busy, setBusy] = useState(false)
  const parseUpload = async (file: File) => {
    if (!campusId) return setStatus('Select or create a campus first.')
    setBusy(true); setStatus('')
    try {
      const text = await file.text(); const lines = text.split(/\r?\n/).filter(Boolean); const headers = lines.shift()?.split(/,|\t/).map(value => value.trim().toLowerCase()) || []
      const index = (names: string[]) => headers.findIndex(header => names.includes(header))
      const records = lines.map(line => { const values = line.split(/,|\t/).map(value => value.trim()); const value = (names: string[], fallback = '') => values[index(names)] ?? fallback; return { recordedAt: value(['recorded_at','date','timestamp'], new Date().toISOString()), buildingName: value(['building_name','building'], 'Campus total'), energyKwh: Number(value(['energy_kwh','energy','kwh'], '0')), cost: Number(value(['cost','energy_cost'], '0')), carbonKg: Number(value(['carbon_kg','carbon','co2'], '0')), occupancy: Number(value(['occupancy','occupancy_percent'], '0')), temperature: Number(value(['temperature','temperature_c'], '0')) } }).filter(record => record.energyKwh > 0)
      const result = await addEnergyRecords(campusId, records); setStatus(`${result.count} readings uploaded successfully.`)
    } catch (error) { setStatus(error instanceof Error ? error.message : 'Upload failed.') } finally { setBusy(false) }
  }
  const seed = async () => { if (!campusId) return setStatus('Select or create a campus first.'); setBusy(true); const result = await seedDemoEnergyData(campusId); setStatus(`${result.count} demo readings added.`); setBusy(false) }
  return <section className="energy-card"><div className="flex items-start justify-between gap-4"><div><p className="flex items-center gap-2 text-sm font-semibold"><Database className="size-4 text-energy-green"/>Campus energy dataset</p><p className="mt-1 text-xs text-muted-foreground">Upload meter readings to power analytics, forecast, anomalies, reports, and simulation baselines.</p></div><FileSpreadsheet className="size-5 text-muted-foreground"/></div><div className="mt-4 flex flex-wrap gap-2"><label className="energy-button-primary cursor-pointer"><Upload className="size-4"/>{busy ? 'Processing...' : 'Upload CSV'}<input type="file" accept=".csv,.txt" className="sr-only" disabled={busy} onChange={event => { const file = event.target.files?.[0]; if (file) void parseUpload(file) }}/></label><button type="button" onClick={() => void seed()} disabled={busy} className="rounded-lg bg-secondary px-3 py-2 text-xs font-medium">Load demo data</button></div>{status && <p className="mt-3 flex items-center gap-2 text-xs text-energy-green"><CheckCircle2 className="size-3.5"/>{status}</p>}<p className="mt-3 text-[11px] text-muted-foreground">Expected columns: recorded_at, building_name, energy_kwh, cost, carbon_kg, occupancy, temperature</p></section>
}
