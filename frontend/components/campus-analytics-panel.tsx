'use client'

import { Activity, BarChart3, Leaf, Zap } from 'lucide-react'
import { useCampusData } from '@/components/campus-data-provider'

export function CampusAnalyticsPanel() {
  const { analytics, selectedCampus, loading, error } = useCampusData()
  const campusName = selectedCampus?.name || ''
  if (loading) return <section className="energy-card"><p className="text-sm font-semibold">Loading campus analytics...</p></section>
  if (error) return <section className="energy-card"><p className="text-sm font-semibold text-destructive">{error}</p></section>
  if (!analytics?.hasData) return <section className="energy-card"><div className="flex items-center gap-3"><Activity className="size-5 text-muted-foreground"/><div><p className="text-sm font-semibold">Analytics waiting for data</p><p className="mt-1 text-xs text-muted-foreground">Upload readings or load demo data to calculate campus KPIs.</p></div></div></section>
  return <section className="flex flex-col gap-3"><div className="flex items-center justify-between"><span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Live campus data · {analytics.readings.toLocaleString()} readings</span><span className="text-[10px] text-muted-foreground">Selected campus source of truth</span></div><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><div className="energy-card"><Zap className="size-4 text-energy-green"/><p className="mt-3 text-2xl font-semibold">{analytics.totalEnergy.toLocaleString()} kWh</p><p className="text-xs text-muted-foreground">{campusName} energy</p></div><div className="energy-card"><BarChart3 className="size-4 text-energy-green"/><p className="mt-3 text-2xl font-semibold">{analytics.savingsPercent}%</p><p className="text-xs text-muted-foreground">modeled savings opportunity</p></div><div className="energy-card"><Leaf className="size-4 text-energy-green"/><p className="mt-3 text-2xl font-semibold">{analytics.totalCarbon.toLocaleString()} kg</p><p className="text-xs text-muted-foreground">carbon footprint</p></div><div className="energy-card"><Activity className="size-4 text-energy-amber"/><p className="mt-3 text-2xl font-semibold">{analytics.anomalies.length}</p><p className="text-xs text-muted-foreground">detected anomalies</p></div></div></section>
}
