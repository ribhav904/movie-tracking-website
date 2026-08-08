"use client";

import { Check, Download, LogOut, Monitor, Moon, ShieldCheck, Sun } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import { isBackendConfigured, isSupabaseConfigured } from "@/lib/config";
import { useAuth } from "@/providers/auth-provider";
import { type ThemePreference, useTheme } from "@/providers/theme-provider";

const themes: Array<{ value: ThemePreference; label: string; icon: typeof Sun }> = [{ value: "light", label: "Light", icon: Sun }, { value: "dark", label: "Dark", icon: Moon }, { value: "system", label: "System", icon: Monitor }];

export default function SettingsPage() {
  const { preference, setPreference } = useTheme();
  const { email, signOut, state } = useAuth();
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const exportData = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const payload = await apiRequest<Record<string, unknown>>("/account/export", { method: "POST" });
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `ledger-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      setExportError(error instanceof Error ? error.message : "Your export could not be created.");
    } finally {
      setExporting(false);
    }
  };
  return <div className="page-stack settings-page">
    <PageHeader eyebrow="Settings" title="Make the archive yours." description="Appearance is local to this device. Account and data controls stay explicit." />
    <section className="settings-section panel"><div><p className="eyebrow">Appearance</p><h2>Theme</h2><p>Choose a lasting preference or follow this device.</p></div><div className="theme-options">{themes.map((theme) => { const Icon = theme.icon; return <button key={theme.value} className={`theme-option ${preference === theme.value ? "is-active" : ""}`} onClick={() => setPreference(theme.value)}><Icon size={18} /><span>{theme.label}</span>{preference === theme.value && <Check size={16} />}</button>; })}</div></section>
    <section className="settings-section panel"><div><p className="eyebrow">Account</p><h2>{email}</h2><p>{state === "preview" ? "Preview mode is local only. Configure Supabase to use a personal account." : "Your password and session are managed by Supabase Auth."}</p>{exportError && <p className="form-error" role="alert">{exportError}</p>}</div><div className="settings-actions"><button className="button button--secondary" disabled={exporting} onClick={() => void exportData()}><Download size={16} /> {exporting ? "Preparing export…" : "Export my data"}</button>{state !== "preview" && <button className="button button--quiet" onClick={() => void signOut()}><LogOut size={16} /> Sign out</button>}</div></section>
    <section className="settings-section setup-panel"><div><ShieldCheck size={19} /><div><p className="eyebrow">Connection status</p><h2>{isBackendConfigured && isSupabaseConfigured ? "Connected to your services" : "Local preview is active"}</h2><p>{isBackendConfigured ? "Application data flows through FastAPI." : "Add the API and Supabase values to frontend/.env.local to connect this interface to your services."}</p></div></div><dl><div><dt>FastAPI</dt><dd>{isBackendConfigured ? "Connected" : "Not configured"}</dd></div><div><dt>Supabase Auth</dt><dd>{isSupabaseConfigured ? "Configured" : "Not configured"}</dd></div></dl></section>
  </div>;
}
