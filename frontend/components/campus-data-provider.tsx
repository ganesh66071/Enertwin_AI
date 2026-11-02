'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { DEMO_CAMPUSES } from '@/lib/demoCampusData'
import { processEnergyAnalytics } from '@/lib/energy-analytics'

type Campus = {
  id: string
  name: string
  location: string
  timezone?: string
  goal?: string
  type?: string
  campus_type?: string
  description?: string | null
}

type Analytics = ReturnType<typeof processEnergyAnalytics>

type CampusOverviewResponse = {
  success: boolean
  campus: Campus
  kpis: {
    total_energy_kwh?: number
    peak_demand_kw?: number
    average_occupancy?: number
    total_cost?: number
    total_co2?: number
    efficiency_score?: number
    record_count?: number
  }
  building_summary?: Array<{
    building_name: string
    total_energy: number
    co2: number
    peak_demand: number
    occupancy: number
    efficiency_score: number
  }>
  data_quality?: { total_records?: number }
}

type CampusDataContextValue = {
  campuses: Campus[]
  selectedCampus?: Campus
  selectedCampusId: string
  analytics: Analytics | null
  loading: boolean
  error: string
  mode: 'demo' | 'dataset'
}

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000/api').replace(/\/$/, '')
const CampusDataContext = createContext<CampusDataContextValue | null>(null)

function mapOverviewToAnalytics(overview: CampusOverviewResponse | null): Analytics | null {
  if (!overview) return null

  const kpis = overview.kpis ?? {}
  const totalEnergy = Number(kpis.total_energy_kwh ?? 0)
  const totalCost = Number(kpis.total_cost ?? 0)
  const totalCarbon = Number(kpis.total_co2 ?? 0)
  const peakValue = Number(kpis.peak_demand_kw ?? 0)
  const averageOccupancy = Number(kpis.average_occupancy ?? 0)
  const baseline = totalEnergy > 0 ? totalEnergy * 1.12 : 0
  const savings = Math.max(0, baseline - totalEnergy)
  const readings = Number(overview.data_quality?.total_records ?? kpis.record_count ?? 0)

  const baseAnalytics = processEnergyAnalytics(
    (overview.building_summary ?? []).flatMap((building) => {
      const readingsPerBuilding = Math.max(1, Math.round((building.total_energy || 0) / Math.max(building.peak_demand || 1, 1)))
      return Array.from({ length: readingsPerBuilding }, (_, index) => ({
        recordedAt: new Date(Date.now() - (index + 1) * 60 * 60 * 1000).toISOString(),
        buildingName: building.building_name,
        energyKwh: Number(building.total_energy ?? 0) / Math.max(readingsPerBuilding, 1),
        cost: Number(building.total_energy ?? 0) * 0.18,
        carbonKg: Number(building.co2 ?? 0) / Math.max(readingsPerBuilding, 1),
        occupancy: Number(building.occupancy ?? 0),
        temperature: 24,
      }))
    })
  )

  const derivedPeak = baseAnalytics.peak ?? { value: 0, at: '', buildingName: '' }

  return {
    ...baseAnalytics,
    hasData: totalEnergy > 0 || readings > 0,
    readings,
    totalEnergy,
    totalCost,
    totalCarbon,
    averageOccupancy,
    baseline,
    savings,
    savingsPercent: baseline ? (savings / baseline) * 100 : 0,
    peak: peakValue > 0 ? { value: peakValue, at: '', buildingName: overview.campus?.name ?? '' } : derivedPeak,
    byBuilding: (overview.building_summary ?? []).map((building) => ({
      buildingName: building.building_name,
      energyKwh: Number(building.total_energy ?? 0),
      cost: Number(building.total_energy ?? 0) * 0.18,
      carbonKg: Number(building.co2 ?? 0),
      readings: 1,
      share: totalEnergy ? (Number(building.total_energy ?? 0) / totalEnergy) * 100 : 0,
    })),
    anomalies: (overview.building_summary ?? []).filter((building) => Number(building.peak_demand ?? 0) > 0).map((building) => ({
      buildingName: building.building_name,
      energyKwh: Number(building.total_energy ?? 0),
      cost: Number(building.total_energy ?? 0) * 0.18,
      carbonKg: Number(building.co2 ?? 0),
      occupancy: Number(building.occupancy ?? 0),
      temperature: 24,
      severity: Number(building.efficiency_score ?? 100) < 70 ? 'warning' : 'info',
    } as any)),
    score: Number(kpis.efficiency_score ?? baseAnalytics.score ?? 0),
  }
}

export function CampusDataProvider({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams()
  const requestedId = searchParams.get('campus') || ''
  const [campuses, setCampuses] = useState<Campus[]>([])
  const [selectedCampusId, setSelectedCampusId] = useState('')
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    const loadCampuses = async () => {
      try {
        setLoading(true)
        const demoCampuses = DEMO_CAMPUSES.map((campus) => ({
          id: campus.id,
          name: campus.name,
          location: campus.location,
          timezone: 'Asia/Kolkata',
          goal: 'Demo campus',
          type: campus.type,
          campus_type: campus.type,
          description: campus.name,
        }))

        const response = await fetch(`${API_BASE}/campuses`, { cache: 'no-store' }).catch(() => null)
        const payload = response ? await response.json().catch(() => null) : null
        const nextCampuses = ((payload?.campuses ?? payload ?? demoCampuses) as Array<any>).length
          ? ((payload?.campuses ?? payload ?? demoCampuses) as Array<any>).map((campus) => ({
              id: campus.id,
              name: campus.name,
              location: campus.location ?? 'Campus location',
              timezone: campus.timezone,
              goal: campus.goal,
              type: campus.campus_type ?? campus.type,
              campus_type: campus.campus_type ?? campus.type,
              description: campus.description ?? null,
            }))
          : demoCampuses

        if (!active) return
        setCampuses(nextCampuses)
        const nextSelectedId = requestedId && nextCampuses.some((campus) => campus.id === requestedId)
          ? requestedId
          : nextCampuses[0]?.id ?? ''
        setSelectedCampusId(nextSelectedId)
        setError('')
      } catch (fetchError) {
        if (!active) return
        setCampuses(DEMO_CAMPUSES.map((campus) => ({
          id: campus.id,
          name: campus.name,
          location: campus.location,
          timezone: 'Asia/Kolkata',
          goal: 'Demo campus',
          type: campus.type,
          campus_type: campus.type,
          description: campus.name,
        })))
        setSelectedCampusId(requestedId || DEMO_CAMPUSES[0]?.id || '')
        setAnalytics(null)
        setError(fetchError instanceof Error ? fetchError.message : 'Unable to load campuses')
      } finally {
        if (active) setLoading(false)
      }
    }

    void loadCampuses()
    return () => {
      active = false
    }
  }, [requestedId])

  useEffect(() => {
    if (!selectedCampusId) {
      setAnalytics(null)
      return
    }

    let active = true
    const loadOverview = async () => {
      try {
        setLoading(true)
        const response = await fetch(`${API_BASE}/campuses/${selectedCampusId}/overview`, { cache: 'no-store' })
        if (!response.ok) throw new Error('Unable to load campus overview')
        const payload = (await response.json()) as CampusOverviewResponse
        if (!active) return
        setAnalytics(mapOverviewToAnalytics(payload))
        setError('')
      } catch (fetchError) {
        if (!active) return
        setAnalytics(null)
        setError(fetchError instanceof Error ? fetchError.message : 'Unable to load campus data')
      } finally {
        if (active) setLoading(false)
      }
    }

    void loadOverview()
    return () => {
      active = false
    }
  }, [selectedCampusId])

  const selectedCampus = campuses.find((campus) => campus.id === selectedCampusId)
  const mode: CampusDataContextValue['mode'] = DEMO_CAMPUSES.some((campus) => campus.id === selectedCampusId) ? 'demo' : 'dataset'

  const value = useMemo<CampusDataContextValue>(
    () => ({
      campuses,
      selectedCampus,
      selectedCampusId,
      analytics,
      loading,
      error,
      mode,
    }),
    [campuses, selectedCampus, selectedCampusId, analytics, loading, error]
  )

  return <CampusDataContext.Provider value={value}>{children}</CampusDataContext.Provider>
}

export function useCampusData() {
  const context = useContext(CampusDataContext)
  if (!context) throw new Error('useCampusData must be used inside CampusDataProvider')
  return context
}
