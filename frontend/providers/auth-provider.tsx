"use client";

import type { Session } from "@supabase/supabase-js";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { isSupabaseConfigured } from "@/lib/config";
import { getSupabaseClient } from "@/lib/supabase";

type AuthState = "loading" | "authenticated" | "signed_out" | "preview";
type AuthContextValue = {
  state: AuthState;
  session: Session | null;
  email: string;
  signIn: (email: string, password: string) => Promise<string | null>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(isSupabaseConfigured ? "loading" : "preview");
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    const supabase = getSupabaseClient();
    if (!supabase) return;
    let active = true;
    void supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      setSession(data.session);
      setState(data.session ? "authenticated" : "signed_out");
    });
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setState(nextSession ? "authenticated" : "signed_out");
    });
    return () => {
      active = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      state,
      session,
      email: session?.user.email ?? "Preview collection",
      signIn: async (email, password) => {
        const supabase = getSupabaseClient();
        if (!supabase) return "Supabase is not configured yet. Add the frontend environment values first.";
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        return error?.message ?? null;
      },
      signOut: async () => {
        await getSupabaseClient()?.auth.signOut();
      },
    }),
    [session, state],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
