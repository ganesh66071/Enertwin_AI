'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Building2, ChevronDown, Plus } from 'lucide-react'
import { useCampusData } from '@/components/campus-data-provider'

type Campus = { id: string; name: string; location: string; timezone?: string; goal?: string; type?: string }

export function CampusSwitcher({ compact = false }: { compact?: boolean }) {
  const router = useRouter()
  const { campuses: contextCampuses, selectedCampus, selectedCampusId } = useCampusData()
  const campuses = contextCampuses as Campus[]
  const selectedId = selectedCampusId
  const [open, setOpen] = useState(false)

  const selected = selectedCampus as Campus | undefined || campuses.find((campus) => campus.id === selectedId)
  return <div className="relative flex items-center gap-2">
    <button type="button" onClick={() => setOpen((value) => !value)} className="flex min-w-0 flex-1 items-center gap-3 rounded-lg bg-white/10 px-3 py-2.5 text-left text-xs text-white hover:bg-white/15">
      <Building2 className="size-4 shrink-0 text-energy-green" />
      <span className={compact ? 'sr-only' : 'min-w-0 flex-1 truncate'}>{selected?.name || 'Select campus'}<ChevronDown className="float-right size-3" /></span>
    </button>
    <Link href="/add-campus" aria-label="Add campus" title="Add campus" className={`${compact ? 'sr-only' : ''} flex size-8 shrink-0 items-center justify-center rounded-lg border border-white/10 text-white/60 hover:bg-white/10 hover:text-white`}><Plus className="size-4" /></Link>
    {open && !compact && <div className="absolute left-0 top-12 z-50 w-64 overflow-hidden rounded-xl border border-white/10 bg-sidebar p-1 shadow-xl">
      {campuses.length ? campuses.map((campus) => <button key={campus.id} type="button" onClick={() => { setOpen(false); router.push(`/dashboard?campus=${encodeURIComponent(campus.id)}`) }} className={`w-full rounded-lg px-3 py-2 text-left text-xs text-white/80 hover:bg-white/10 ${campus.id === selectedId ? 'bg-white/10' : ''}`}><span className="block font-medium">{campus.name}</span><span className="block text-[10px] text-white/45">{campus.location}</span></button>) : <p className="px-3 py-3 text-xs text-white/50">No campuses saved yet.</p>}
    </div>}
  </div>
}
