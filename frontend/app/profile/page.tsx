import { auth } from '@/lib/auth'
import Link from 'next/link'
import { headers } from 'next/headers'
import { redirect } from 'next/navigation'
import { ArrowLeft, Mail, UserRound } from 'lucide-react'

export default async function ProfilePage() {
  const session = await auth.api.getSession({ headers: await headers() })
  if (!session?.user) redirect('/sign-in')
  const name = session.user.name || 'Workspace member'
  const initials = name.split(' ').map(part => part[0]).join('').slice(0, 2).toUpperCase()
  return <main className="min-h-screen bg-background px-5 py-8 lg:px-8"><div className="mx-auto max-w-3xl"><Link href="/dashboard" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4"/>Back to dashboard</Link><div className="mt-8"><p className="text-xs font-medium uppercase tracking-[0.16em] text-[var(--energy-green)]">Account</p><h1 className="mt-2 text-3xl font-semibold tracking-tight text-[var(--sidebar)]">Your profile</h1><p className="mt-2 text-sm text-muted-foreground">The account details connected to your EnerTwin workspace.</p></div><section className="mt-8 overflow-hidden rounded-2xl border border-border bg-card shadow-sm"><div className="flex flex-col gap-5 border-b border-border bg-[var(--sidebar)] p-6 text-white sm:flex-row sm:items-center"><div className="flex size-16 items-center justify-center rounded-full bg-[var(--energy-green)] text-xl font-semibold">{initials}</div><div><h2 className="text-xl font-semibold">{name}</h2><p className="mt-1 text-sm text-white/60">Authenticated EnerTwin user</p></div></div><div className="grid gap-4 p-6 sm:grid-cols-2"><div className="rounded-xl bg-secondary p-4"><div className="flex items-center gap-2 text-muted-foreground"><UserRound className="size-4"/><span className="text-xs font-medium">Full name</span></div><p className="mt-3 text-sm font-semibold">{name}</p></div><div className="rounded-xl bg-secondary p-4"><div className="flex items-center gap-2 text-muted-foreground"><Mail className="size-4"/><span className="text-xs font-medium">Email address</span></div><p className="mt-3 break-all text-sm font-semibold">{session.user.email}</p></div></div></section></div></main>
}
