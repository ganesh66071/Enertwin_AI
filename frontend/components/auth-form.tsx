'use client'

import { FormEvent, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { AlertCircle, ArrowRight, Loader2, Zap } from 'lucide-react'
import { authClient } from '@/lib/auth-client'

export function AuthForm({ mode }: { mode: 'sign-in' | 'sign-up' }) {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const isSignUp = mode === 'sign-up'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPending(true)
    setError('')
    const result = isSignUp
      ? await authClient.signUp.email({ name, email, password })
      : await authClient.signIn.email({ email, password })
    setPending(false)
    if (result.error) {
      setError(result.error.message || 'Unable to authenticate with those credentials.')
      return
    }
    router.push('/dashboard')
    router.refresh()
  }

  return <main className="flex min-h-screen items-center justify-center bg-background px-5 py-12"><div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-border bg-card shadow-xl lg:grid-cols-[0.85fr_1.15fr]"><aside className="hidden flex-col justify-between bg-[var(--sidebar)] p-10 text-white lg:flex"><div><Link href="/" className="flex items-center gap-3 font-semibold"><span className="flex size-10 items-center justify-center rounded-lg bg-white/10 text-[var(--energy-green)]"><Zap className="size-5"/></span>EnerTwin <span className="text-[var(--energy-green)]">AI</span></Link><p className="mt-20 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--energy-green)]">Energy intelligence</p><h1 className="mt-4 text-4xl font-semibold leading-tight">Make every building decision measurable.</h1><p className="mt-5 text-sm leading-relaxed text-white/65">Connect campus data, digital twins, and AI recommendations in one calm operational workspace.</p></div><p className="text-xs text-white/45">Northbridge Campus workspace</p></aside><section className="p-7 sm:p-10"><Link href="/" className="text-sm text-muted-foreground hover:text-foreground">← Back to home</Link><div className="mt-10"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--energy-green)]">{isSignUp ? 'Create workspace access' : 'Welcome back'}</p><h2 className="mt-3 text-3xl font-semibold text-[var(--sidebar)]">{isSignUp ? 'Start with EnerTwin AI' : 'Sign in to your workspace'}</h2><p className="mt-2 text-sm text-muted-foreground">{isSignUp ? 'Create your operator account to manage campuses and digital twins.' : 'Continue managing your campus energy model.'}</p></div><form onSubmit={submit} className="mt-8 flex flex-col gap-4">{isSignUp && <label className="flex flex-col gap-2 text-sm font-medium">Full name<input required value={name} onChange={event => setName(event.target.value)} className="h-11 rounded-lg border border-input bg-background px-3 font-normal outline-none focus:ring-2 focus:ring-ring" placeholder="Alex Morgan"/></label>}<label className="flex flex-col gap-2 text-sm font-medium">Email<input required type="email" value={email} onChange={event => setEmail(event.target.value)} className="h-11 rounded-lg border border-input bg-background px-3 font-normal outline-none focus:ring-2 focus:ring-ring" placeholder="you@university.edu"/></label><label className="flex flex-col gap-2 text-sm font-medium">Password<input required minLength={8} type="password" value={password} onChange={event => setPassword(event.target.value)} className="h-11 rounded-lg border border-input bg-background px-3 font-normal outline-none focus:ring-2 focus:ring-ring" placeholder="At least 8 characters"/></label>{error && <div role="alert" className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="size-4"/>{error}</div>}<button disabled={pending} className="energy-button-primary mt-2 w-full disabled:opacity-60">{pending ? <Loader2 className="size-4 animate-spin"/> : null}{isSignUp ? 'Create account' : 'Sign in'}{!pending && <ArrowRight className="size-4"/>}</button></form><p className="mt-7 text-center text-sm text-muted-foreground">{isSignUp ? 'Already have an account?' : 'New to EnerTwin AI?'} <Link href={isSignUp ? '/sign-in' : '/sign-up'} className="font-semibold text-[var(--sidebar)] underline underline-offset-4">{isSignUp ? 'Sign in' : 'Create an account'}</Link></p></section></div></main>
}
