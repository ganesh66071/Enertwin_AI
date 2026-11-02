'use server'

import { auth } from '@/lib/auth'
import { db } from '@/lib/db'
import { headers } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { randomUUID } from 'crypto'
import { sql } from 'drizzle-orm'

type CampusInput = { name: string; location: string; timezone: string; goal: string; buildings: { name: string; type: string; floors: string; area: string; occupancy: string }[]; energyRecords?: { recordedAt: string; buildingName: string; energyKwh: number; cost: number; carbonKg: number; occupancy: number; temperature: number }[] }

async function getUserId() {
  const session = await auth.api.getSession({ headers: await headers() })
  if (!session?.user) throw new Error('Unauthorized')
  return session.user.id
}

export async function createCampus(input: CampusInput) {
  const userId = await getUserId()
  const campusId = randomUUID()
  await db.execute(sql`INSERT INTO "campus" ("id", "userId", "name", "location", "timezone", "goal") VALUES (${campusId}, ${userId}, ${input.name.trim()}, ${input.location.trim()}, ${input.timezone}, ${input.goal})`)
  for (const building of input.buildings.filter(item => item.name.trim())) {
    await db.execute(sql`INSERT INTO "building" ("id", "campusId", "userId", "name", "type", "floors", "area", "occupancy") VALUES (${randomUUID()}, ${campusId}, ${userId}, ${building.name.trim()}, ${building.type}, ${Number(building.floors) || 1}, ${Number(building.area) || 0}, ${Number(building.occupancy) || 0})`)
  }
  for (const record of (input.energyRecords || []).slice(0, 5000)) {
    await db.execute(sql`INSERT INTO "energy_dataset" ("id", "campusId", "userId", "recordedAt", "buildingName", "energyKwh", "cost", "carbonKg", "occupancy", "temperature", "source") VALUES (${randomUUID()}, ${campusId}, ${userId}, ${record.recordedAt}, ${record.buildingName}, ${record.energyKwh}, ${record.cost}, ${record.carbonKg}, ${record.occupancy}, ${record.temperature}, ${'dataset'})`)
  }
  revalidatePath('/dashboard')
  return { id: campusId, name: input.name.trim() }
}

export async function getCampuses() {
  const userId = await getUserId()
  const result = await db.execute(sql`SELECT "id", "name", "location", "timezone", "goal" FROM "campus" WHERE "userId" = ${userId} ORDER BY "createdAt" DESC`)
  return (result.rows || []) as { id: string; name: string; location: string; timezone: string; goal: string }[]
}

export async function getCampusBuildings(campusId: string) {
  const userId = await getUserId()
  const result = await db.execute(sql`SELECT "id", "name", "type", "floors", "area", "occupancy" FROM "building" WHERE "campusId" = ${campusId} AND "userId" = ${userId} ORDER BY "createdAt" ASC`)
  return result.rows || []
}
