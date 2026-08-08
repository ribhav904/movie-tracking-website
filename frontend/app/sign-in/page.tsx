"use client";

import { ArrowRight, LockKeyhole } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { isSupabaseConfigured } from "@/lib/config";
import { useAuth } from "@/providers/auth-provider";

export default function SignInPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    const message = await signIn(String(form.get("email")), String(form.get("password")));
    setSubmitting(false);
    if (message) setError(message); else router.replace("/");
  }
  return <main className="sign-in"><section className="sign-in__intro"><Link href="/" className="brand"><span className="brand__mark">L</span><span><strong>Ledger</strong><small>Entertainment archive</small></span></Link><div><p className="eyebrow">A private record</p><h1>Keep what moved you close.</h1><p>Films, television, games, and books in one clear personal archive.</p></div><p className="sign-in__footnote">No public profile. No social feed. Just your history and your next choice.</p></section><section className="sign-in__form-wrap"><form className="sign-in__form" onSubmit={onSubmit}><LockKeyhole size={20} /><p className="eyebrow">Sign in</p><h2>Welcome back.</h2>{isSupabaseConfigured ? <><label>Email<input type="email" name="email" autoComplete="email" required /></label><label>Password<input type="password" name="password" autoComplete="current-password" required /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="button button--primary" disabled={submitting}>{submitting ? "Signing in…" : <>Continue <ArrowRight size={16} /></>}</button></> : <div className="setup-message"><h3>Connection details are needed.</h3><p>Set the Supabase URL, publishable key, and FastAPI URL in <code>frontend/.env.local</code>. Until then, you can inspect the interface with local preview data.</p><Link href="/" className="button button--secondary">Open preview <ArrowRight size={16} /></Link></div>}</form></section></main>;
}
