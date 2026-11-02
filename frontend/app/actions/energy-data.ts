'use server'

import { headers } from 'next/headers'
import { randomUUID } from 'crypto'
import { sql } from 'drizzle-orm'
import { auth } from '@/lib/auth'
import { db } from '@/lib/db'

type EnergyRecord = { recordedAt: string; buildingName: string; energyKwh: number; cost: number; carbonKg: number; occupancy: number; temperature: number }

async function getUserId() {
  const session = await auth.api.getSession({ headers: await headers() })
  if (!session?.user) throw new Error('Unauthorized')
  return session.user.id
}

export async function addEnergyRecords(campusId: string, records: EnergyRecord[], source = 'upload') {
  const userId = await getUserId()
  if (!campusId || records.length === 0) throw new Error('Campus and at least one valid reading are required')
  for (const record of records.slice(0, 5000)) {
    await db.execute(sql`INSERT INTO "energy_dataset" ("id", "campusId", "userId", "recordedAt", "buildingName", "energyKwh", "cost", "carbonKg", "occupancy", "temperature", "source") VALUES (${randomUUID()}, ${campusId}, ${userId}, ${record.recordedAt}, ${record.buildingName}, ${record.energyKwh}, ${record.cost}, ${record.carbonKg}, ${record.occupancy}, ${record.temperature}, ${source})`)
  }
  return { count: Math.min(records.length, 5000) }
}

export async function getEnergyRecords(campusId: string) {
  const userId = await getUserId()
  const result = await db.execute(sql`SELECT "recordedAt", "buildingName", "energyKwh", "cost", "carbonKg", "occupancy", "temperature", "source" FROM "energy_dataset" WHERE "campusId" = ${campusId} AND "userId" = ${userId} ORDER BY "recordedAt" ASC`)
  return result.rows
}

export async function seedDemoEnergyData(campusId: string) {
  const records: EnergyRecord[] = []
  const buildings = ['Mechanical Block', 'Innovation Centre', 'North Residence', 'Library & Archive']
  for (let day = 0; day < 30; day += 1) for (let hour = 0; hour < 24; hour += 1) for (let index = 0; index < buildings.length; index += 1) {
    const base = [180, 142, 96, 78][index]
    const daylight = Math.max(0, Math.sin(((hour - 6) / 12) * Math.PI))
    const weekday = day % 7 < 5 ? 1 : 0.68
    const energyKwh = Math.round((base * (0.62 + daylight * 0.48) * weekday) * 10) / 10
    records.push({ recordedAt: `2025-10-${String(day + 1).padStart(2, '0')}T${String(hour).padStart(2, '0')}:00:00`, buildingName: buildings[index], energyKwh, cost: Math.round(energyKwh * 0.18 * 100) / 100, carbonKg: Math.round(energyKwh * 0.42 * 100) / 100, occupancy: Math.round((18 + daylight * 62) * weekday), temperature: Math.round((18 + daylight * 7) * 10) / 10 })
  }
  return addEnergyRecords(campusId, records, 'demo')
}
