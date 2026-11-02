import { Suspense } from 'react'
import EnerTwinApp from '@/components/ener-twin-app'
import { CampusDataProvider } from '@/components/campus-data-provider'

export default function SlugPage() {
  return <Suspense fallback={<div className="min-h-screen bg-background" />}><CampusDataProvider><EnerTwinApp /></CampusDataProvider></Suspense>
}
